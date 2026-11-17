
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Bug, Comment, User, UserRole
from app.schemas import CommentCreate, CommentUpdate, CommentRead
from app.core.security import get_current_user


router = APIRouter(
    prefix="/api",
    tags=["Bug Comments"],
)


def get_accessible_bug(
    bug_id: int,
    current_user: User,
    db: Session,
) -> Bug:
    bug = db.scalar(
        select(Bug).where(
            Bug.id == bug_id,
            (
                (Bug.reporter_id == current_user.id)
                | (Bug.assignee_id == current_user.id)
                | (current_user.role == UserRole.ADMIN)
            ),
        )
    )

    if bug is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bug not found or you do not have permission to access it",
        )

    return bug


def get_comment(
    comment_id: int,
    current_user: User,
    db: Session,
) -> Comment:
    comment = db.get(Comment, comment_id)

    if comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )

    get_accessible_bug(
        comment.bug_id,
        current_user,
        db,
    )

    return comment


@router.post(
    "/bugs/{bug_id}/comments",
    response_model=CommentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_comment(
    bug_id: int,
    comment_data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_accessible_bug(bug_id, current_user, db)

    new_comment = Comment(
        content=comment_data.content.strip(),
        bug_id=bug_id,
        user_id=current_user.id,
    )

    if not new_comment.content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Comment cannot be empty",
        )

    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    return new_comment


@router.get(
    "/bugs/{bug_id}/comments",
    response_model=list[CommentRead],
)
def get_bug_comments(
    bug_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_accessible_bug(bug_id, current_user, db)

    statement = (
        select(Comment)
        .where(Comment.bug_id == bug_id)
        .order_by(Comment.created_at.asc())
    )

    return db.scalars(statement).all()


@router.put(
    "/comments/{comment_id}",
    response_model=CommentRead,
)
def update_comment(
    comment_id: int,
    comment_data: CommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    comment = get_comment(comment_id, current_user, db)

    if (
        comment.user_id != current_user.id
        and current_user.role != UserRole.ADMIN
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own comments",
        )

    updated_content = comment_data.content.strip()

    if not updated_content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Comment cannot be empty",
        )

    comment.content = updated_content

    db.commit()
    db.refresh(comment)

    return comment


@router.delete(
    "/comments/{comment_id}",
)
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    comment = get_comment(comment_id, current_user, db)

    if (
        comment.user_id != current_user.id
        and current_user.role != UserRole.ADMIN
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own comments",
        )

    db.delete(comment)
    db.commit()

    return {
        "message": "Comment deleted successfully",
        "comment_id": comment_id,
    }
