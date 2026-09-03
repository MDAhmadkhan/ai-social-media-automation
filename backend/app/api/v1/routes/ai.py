from fastapi import APIRouter, Depends, HTTPException
import structlog

from app.core.deps import get_current_user, get_repositories, require_roles
from app.models.domain import User
from app.models.enums import UserRole
from app.repositories.factory import Repositories
from app.schemas.common import BulkGenerateRequest, GenerateRequest, PromptGenerateRequest, TopicBulkGenerateRequest
from app.services.ai.ai_service import AIService

router = APIRouter()
logger = structlog.get_logger()


@router.post("/generate")
async def generate(
    payload: GenerateRequest,
    user: User = Depends(require_roles(UserRole.admin, UserRole.manager, UserRole.editor)),
    repos: Repositories = Depends(get_repositories),
):
    try:
        return await AIService(repos).generate_for_content(str(user.id), payload.content_item_id, payload.platforms, payload.generate_images)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("ai_generation_failed", user_id=str(user.id), content_item_id=payload.content_item_id)
        raise HTTPException(status_code=500, detail="AI generation failed unexpectedly. Check backend logs for details.") from exc


@router.post("/generate-from-prompt")
async def generate_from_prompt(
    payload: PromptGenerateRequest,
    user: User = Depends(require_roles(UserRole.admin, UserRole.manager, UserRole.editor)),
    repos: Repositories = Depends(get_repositories),
):
    try:
        return await AIService(repos).generate_from_prompt(
            str(user.id),
            payload.prompt,
            payload.title,
            payload.platforms,
            payload.generate_images,
            payload.image_prompt,
        )
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("prompt_generation_failed", user_id=str(user.id))
        raise HTTPException(status_code=500, detail="Prompt generation failed unexpectedly. Check backend logs for details.") from exc


@router.post("/generate-topic-pack")
async def generate_topic_pack(
    payload: TopicBulkGenerateRequest,
    user: User = Depends(require_roles(UserRole.admin, UserRole.manager, UserRole.editor)),
    repos: Repositories = Depends(get_repositories),
):
    try:
        return await AIService(repos).generate_topic_pack(str(user.id), payload.topic, payload.platforms, payload.count)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("topic_pack_generation_failed", user_id=str(user.id))
        raise HTTPException(status_code=500, detail="Topic pack generation failed unexpectedly. Check backend logs for details.") from exc


@router.get("/generated-posts")
async def generated_posts(user: User = Depends(get_current_user), repos: Repositories = Depends(get_repositories)):
    return await repos.generated_posts.list({"owner_id": str(user.id)}, limit=200, sort=[("created_at", -1)])


@router.post("/generate-bulk")
async def generate_bulk(
    payload: BulkGenerateRequest,
    user: User = Depends(require_roles(UserRole.admin, UserRole.manager, UserRole.editor)),
    repos: Repositories = Depends(get_repositories),
):
    content_items = await repos.content_items.list({"owner_id": str(user.id)}, limit=payload.limit, sort=[("created_at", -1)])
    generated = []
    errors = []
    service = AIService(repos)
    for item in content_items:
        try:
            generated.extend(await service.generate_for_content(str(user.id), str(item.id), payload.platforms, payload.generate_images))
        except (ValueError, RuntimeError) as exc:
            errors.append({"content_item_id": str(item.id), "title": item.title, "error": str(exc)})
        except Exception as exc:
            logger.exception("ai_bulk_generation_failed", user_id=str(user.id), content_item_id=str(item.id))
            errors.append({"content_item_id": str(item.id), "title": item.title, "error": "AI generation failed unexpectedly. Check backend logs for details."})
    return {"generated_count": len(generated), "errors": errors, "posts": generated}
