from sqlalchemy.orm import Session
from typing import Generic, TypeVar, Type, List, Optional, Any, Dict, Union
from pydantic import BaseModel

from ..models.base import Base

# Define a type variable for SQLAlchemy models
ModelType = TypeVar("ModelType", bound=Base)
# Define a type variable for Pydantic schemas
SchemaType = TypeVar("SchemaType", bound=BaseModel)

class BaseController(Generic[ModelType, SchemaType]):
    """
    Base controller with CRUD operations for all models
    """
    
    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    def get(self, db: Session, id: int) -> Optional[ModelType]:
        """Get a single record by ID"""
        return db.query(self.model).filter(self.model.id == id).first()
    
    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Get multiple records with pagination"""
        return db.query(self.model).offset(skip).limit(limit).all()
    
    def create(self, db: Session, obj_in: Union[SchemaType, Dict[str, Any]]) -> ModelType:
        """Create a new record"""
        if isinstance(obj_in, dict):
            obj_data = obj_in
        else:
            obj_data = obj_in.dict(exclude_unset=True)
            
        db_obj = self.model(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(self, db: Session, db_obj: ModelType, obj_in: Union[SchemaType, Dict[str, Any]]) -> ModelType:
        """Update an existing record"""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
            
        for field in update_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, update_data[field])
                
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def delete(self, db: Session, id: int) -> ModelType:
        """Delete a record"""
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        return obj