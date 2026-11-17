
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Bug, User, UserRole, BugStatus, BugPriority
from app.schemas import BugCreate, BugUpdate, BugRead, BugAssign
from app.core.security import get_current_user


router = APIRouter(
    prefix="/api/bugs",
    tags=["Bug Management"],
)


def get_accessible_bug(
    bug_id: int,
    current_user: User,
    db: Session,
) -> Bug:
    bug = db.scalar(
        select(Bug).where(
            Bug.id == bug_id,
            or_(
                Bug.reporter_id == current_user.id,
                Bug.assignee_id == current_user.id,
                current_user.role == UserRole.ADMIN,
            ),
        )
    )

    if bug is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bug not found or you do not have permission to view it",
        )

    return bug


@router.post(
    "/",
    response_model=BugRead,
    status_code=status.HTTP_201_CREATED,
)
def create_bug(
    bug_data: BugCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_bug = Bug(
        title=bug_data.title.strip(),
        description=bug_data.description.strip(),
        priority=bug_data.priority,
        status=BugStatus.OPEN,
        reporter_id=current_user.id,
    )

    db.add(new_bug)
    db.commit()
    db.refresh(new_bug)

    return new_bug


@router.get("/", response_model=list[BugRead])
def get_all_bugs(
    bug_status: BugStatus | None = None,
    priority: BugPriority | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    statement = select(Bug).where(
        or_(
            Bug.reporter_id == current_user.id,
            Bug.assignee_id == current_user.id,
            current_user.role == UserRole.ADMIN,
        )
    )

    if bug_status is not None:
        statement = statement.where(
            Bug.status == bug_status
        )

    if priority is not None:
        statement = statement.where(
            Bug.priority == priority
        )

    if search and search.strip():
        statement = statement.where(
            Bug.title.ilike(f"%{search.strip()}%")
        )

    statement = statement.order_by(
        Bug.created_at.desc()
    )

    return db.scalars(statement).all()


@router.get("/{bug_id}", response_model=BugRead)
def get_bug(
    bug_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_accessible_bug(bug_id, current_user, db)


@router.put("/{bug_id}", response_model=BugRead)
def update_bug(
    bug_id: int,
    bug_data: BugUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bug = get_accessible_bug(bug_id, current_user, db)

    if (
        bug.reporter_id != current_user.id
        and current_user.role != UserRole.ADMIN
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the bug reporter or an Admin can update this bug",
        )

    update_data = bug_data.model_dump(
        exclude_unset=True,
        exclude_none=True,
    )

    if "title" in update_data:
        update_data["title"] = update_data["title"].strip()

    if "description" in update_data:
        update_data["description"] = update_data["description"].strip()

    for field, value in update_data.items():
        setattr(bug, field, value)

    db.commit()
    db.refresh(bug)

    return bug


@router.delete("/{bug_id}")
def delete_bug(
    bug_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bug = get_accessible_bug(bug_id, current_user, db)

    if (
        bug.reporter_id != current_user.id
        and current_user.role != UserRole.ADMIN
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the bug reporter or an Admin can delete this bug",
        )

    db.delete(bug)
    db.commit()

    return {
        "message": "Bug deleted successfully",
        "bug_id": bug_id,
    }


@router.post(
    "/{bug_id}/assign",
    response_model=BugRead,
)
def assign_bug(
    bug_id: int,
    assignment_data: BugAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Admin users can assign bugs",
        )

    bug = db.get(Bug, bug_id)

    if bug is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bug not found",
        )

    if assignment_data.assignee_id is None:
        bug.assignee_id = None

    else:
        assignee = db.scalar(
            select(User).where(
                User.id == assignment_data.assignee_id,
                User.is_active.is_(True),
                User.role.in_([
                    UserRole.DEVELOPER,
                    UserRole.TESTER,
                ]),
            )
        )

        if assignee is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignee must be an active Developer or Tester",
            )

        bug.assignee_id = assignee.id

    db.commit()
    db.refresh(bug)

    return bug
