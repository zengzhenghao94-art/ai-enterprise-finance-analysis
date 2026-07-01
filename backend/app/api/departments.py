"""部门查询 API"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Department
from ..schemas import DepartmentOut, DepartmentListResponse

router = APIRouter(prefix="/api/departments", tags=["departments"])


@router.get("", response_model=DepartmentListResponse)
def list_departments(db: Session = Depends(get_db)):
    """获取所有部门列表"""
    rows = db.query(Department).all()
    return DepartmentListResponse(
        data=[DepartmentOut.model_validate(d) for d in rows]
    )
