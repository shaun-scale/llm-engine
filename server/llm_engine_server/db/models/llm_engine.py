from datetime import datetime
from typing import Any, Dict, List, Optional

from pytz import timezone
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    select,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship, selectinload
from sqlalchemy.sql import func, text
from sqlalchemy.sql.expression import update
from sqlalchemy.sql.schema import CheckConstraint, Index, UniqueConstraint
from xid import XID

from ..base import Base
from .constants import LONG_STRING, SHORT_STRING

AUTOGENERATED_FIELDS = ["id", "created_at"]
UTC = timezone("UTC")


def get_xid():
    return XID().string()


def time_now():
    return datetime.now(UTC)


class Bundle(Base):
    __tablename__ = "bundles"
    __table_args__ = (
        CheckConstraint(
            "flavor IN ('cloudpickle_artifact', 'zip_artifact', "
            "'runnable_image', 'streaming_enhanced_runnable_image', 'triton_enhanced_runnable_image')"
        ),
        CheckConstraint("(flavor like '%_artifact') = (artifact_requirements IS NOT NULL)"),
        CheckConstraint("(flavor like '%_artifact') = (artifact_location IS NOT NULL)"),
        CheckConstraint("(flavor like '%_artifact') = (artifact_framework_type IS NOT NULL)"),
        CheckConstraint(
            "(artifact_framework_type = 'pytorch') = (artifact_pytorch_image_tag IS NOT NULL)"
        ),
        CheckConstraint(
            "(artifact_framework_type = 'tensorflow') = (artifact_tensorflow_version IS NOT NULL)"
        ),
        CheckConstraint(
            "(artifact_framework_type = 'custom_base_image') = (artifact_image_repository IS NOT NULL)"
        ),
        CheckConstraint(
            "(artifact_framework_type = 'custom_base_image') = (artifact_image_tag IS NOT NULL)"
        ),
        CheckConstraint(
            "(flavor = 'cloudpickle_artifact') = (cloudpickle_artifact_load_predict_fn IS NOT NULL)"
        ),
        CheckConstraint(
            "(flavor = 'cloudpickle_artifact') = (cloudpickle_artifact_load_model_fn IS NOT NULL)"
        ),
        CheckConstraint(
            "(flavor = 'zip_artifact') = (zip_artifact_load_predict_fn_module_path IS NOT NULL)"
        ),
        CheckConstraint(
            "(flavor = 'zip_artifact') = (zip_artifact_load_model_fn_module_path IS NOT NULL)"
        ),
        CheckConstraint(
            "(flavor like '%runnable_image') = (runnable_image_repository IS NOT NULL)"
        ),
        CheckConstraint("(flavor like '%runnable_image') = (runnable_image_tag IS NOT NULL)"),
        CheckConstraint("(flavor like '%runnable_image') = (runnable_image_command IS NOT NULL)"),
        CheckConstraint(
            "(flavor like '%runnable_image') = (runnable_image_predict_route IS NOT NULL)"
        ),
        CheckConstraint(
            "(flavor like '%runnable_image') = (runnable_image_healthcheck_route IS NOT NULL)"
        ),
        CheckConstraint("(flavor like '%runnable_image') = (runnable_image_env::text != 'null')"),
        CheckConstraint("(flavor like '%runnable_image') = (runnable_image_protocol IS NOT NULL)"),
        # This one requires a backfill because there are already runnable images in the DB
        # that do not have this field set.
        # CheckConstraint("(flavor like '%runnable_image') = (runnable_image_readiness_initial_delay_seconds IS NOT NULL)"),
        CheckConstraint(
            "(flavor = 'streaming_enhanced_runnable_image') = (streaming_enhanced_runnable_image_streaming_command IS NOT NULL)"
        ),
        CheckConstraint(
            "(flavor = 'streaming_enhanced_runnable_image') = (streaming_enhanced_runnable_image_streaming_predict_route IS NOT NULL)"
        ),
        CheckConstraint(
            "(flavor = 'triton_enhanced_runnable_image') = (triton_enhanced_runnable_image_model_repository IS NOT NULL)"
        ),
        CheckConstraint(
            "(flavor = 'triton_enhanced_runnable_image') = (triton_enhanced_runnable_image_num_cpu IS NOT NULL)"
        ),
        CheckConstraint(
            "(flavor = 'triton_enhanced_runnable_image') = (triton_enhanced_runnable_image_commit_tag IS NOT NULL)"
        ),
        CheckConstraint(
            "(flavor = 'triton_enhanced_runnable_image') = (triton_enhanced_runnable_image_readiness_initial_delay_seconds IS NOT NULL)"
        ),
        {"schema": "llm_engine"},
    )

    id = Column(Text, primary_key=True)
    name = Column(String(LONG_STRING), index=True, nullable=False)
    created_by = Column(String(SHORT_STRING), index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    bundle_metadata = Column(JSON, default={}, nullable=False)
    model_artifact_ids = Column(ARRAY(Text), server_default="{}")
    schema_location = Column(Text, nullable=True)
    owner = Column(String(SHORT_STRING), nullable=False)
    # TODO: remove the default once we have a way to populate this field.
    flavor = Column(Text, index=True, nullable=False, default="cloudpickle_artifact")

    # Artifact (Cloudpickle or Zip) fields and constraints
    artifact_requirements = Column(ARRAY(Text), nullable=True)
    artifact_location = Column(Text, nullable=True)
    artifact_app_config = Column(JSON, nullable=True)
    artifact_framework_type = Column(Text, nullable=True)
    artifact_pytorch_image_tag = Column(Text, nullable=True)
    artifact_tensorflow_version = Column(Text, nullable=True)
    artifact_image_repository = Column(Text, nullable=True)
    artifact_image_tag = Column(Text, nullable=True)

    # Cloudpickle Artifact fields
    cloudpickle_artifact_load_predict_fn = Column(Text, nullable=True)
    cloudpickle_artifact_load_model_fn = Column(Text, nullable=True)

    # Zip Artifact fields
    zip_artifact_load_predict_fn_module_path = Column(Text, nullable=True)
    zip_artifact_load_model_fn_module_path = Column(Text, nullable=True)

    # Runnable Image fields
    runnable_image_repository = Column(Text, nullable=True)
    runnable_image_tag = Column(Text, nullable=True)
    runnable_image_command = Column(ARRAY(Text), nullable=True)
    runnable_image_predict_route = Column(Text, nullable=True)
    runnable_image_healthcheck_route = Column(Text, nullable=True)
    runnable_image_env = Column(JSON, nullable=True)
    runnable_image_protocol = Column(Text, nullable=True)
    runnable_image_readiness_initial_delay_seconds = Column(Integer, nullable=True)

    # Streaming Enhanced Runnable Image fields
    streaming_enhanced_runnable_image_streaming_command = Column(ARRAY(Text), nullable=True)
    streaming_enhanced_runnable_image_streaming_predict_route = Column(Text, nullable=True)

    # Triton Enhanced Runnable Image fields
    triton_enhanced_runnable_image_model_repository = Column(Text, nullable=True)
    triton_enhanced_runnable_image_model_replicas = Column(JSON, nullable=True)
    triton_enhanced_runnable_image_num_cpu = Column(Numeric, nullable=True)
    triton_enhanced_runnable_image_commit_tag = Column(Text, nullable=True)
    triton_enhanced_runnable_image_storage = Column(Text, nullable=True)
    triton_enhanced_runnable_image_memory = Column(Text, nullable=True)
    triton_enhanced_runnable_image_readiness_initial_delay_seconds = Column(Integer, nullable=True)

    # LEGACY FIELDS
    # These fields are no longer used, but are kept around for backwards compatibility.
    # They may be deleted after backfilling the new fields, which duplicates the data.
    location = Column(Text)  # FIXME: Delete
    version = Column(String(SHORT_STRING))  # FIXME: Delete
    registered_model_name = Column(Text, nullable=True)  # FIXME: Delete
    requirements = Column(JSON)  # FIXME: Delete
    env_params = Column(JSON)  # FIXME: Delete
    packaging_type = Column(Text, default="cloudpickle")  # FIXME: Delete
    app_config = Column(JSON, nullable=True)  # FIXME: Delete

    def __init__(
        self,
        *,
        name: Optional[str] = None,
        created_by: Optional[str] = None,
        owner: Optional[str] = None,
        schema_location: Optional[str] = None,
        model_artifact_ids: Optional[List[str]] = None,
        bundle_metadata: Optional[Dict[str, Any]] = None,
        flavor: Optional[str] = None,
        # Artifact fields
        artifact_requirements: Optional[List[str]] = None,
        artifact_location: Optional[str] = None,
        artifact_app_config: Optional[Dict[str, Any]] = None,
        artifact_framework_type: Optional[str] = None,
        artifact_pytorch_image_tag: Optional[str] = None,
        artifact_tensorflow_version: Optional[str] = None,
        artifact_image_repository: Optional[str] = None,
        artifact_image_tag: Optional[str] = None,
        # Cloudpickle Artifact fields
        cloudpickle_artifact_load_predict_fn: Optional[str] = None,
        cloudpickle_artifact_load_model_fn: Optional[str] = None,
        # Zip Artifact fields
        zip_artifact_load_predict_fn_module_path: Optional[str] = None,
        zip_artifact_load_model_fn_module_path: Optional[str] = None,
        # Runnable Image fields
        runnable_image_repository: Optional[str] = None,
        runnable_image_tag: Optional[str] = None,
        runnable_image_command: Optional[List[str]] = None,
        runnable_image_predict_route: Optional[str] = None,
        runnable_image_healthcheck_route: Optional[str] = None,
        runnable_image_env: Optional[Dict[str, Any]] = None,
        runnable_image_protocol: Optional[str] = None,
        runnable_image_readiness_initial_delay_seconds: Optional[int] = None,
        # Streaming Enhanced Runnable Image fields
        streaming_enhanced_runnable_image_streaming_command: Optional[List[str]] = None,
        streaming_enhanced_runnable_image_streaming_predict_route: Optional[str] = None,
        # Triton Enhanced Runnable Image fields
        triton_enhanced_runnable_image_model_repository: Optional[str] = None,
        triton_enhanced_runnable_image_model_replicas: Optional[Dict[str, str]] = None,
        triton_enhanced_runnable_image_num_cpu: Optional[float] = None,
        triton_enhanced_runnable_image_commit_tag: Optional[str] = None,
        triton_enhanced_runnable_image_storage: Optional[str] = None,
        triton_enhanced_runnable_image_memory: Optional[str] = None,
        triton_enhanced_runnable_image_readiness_initial_delay_seconds: Optional[int] = None,
        # Legacy fields
        location: Optional[str] = None,
        version: Optional[str] = None,
        registered_model_name: Optional[str] = None,
        requirements: Optional[List[str]] = None,
        env_params: Optional[Dict[str, Any]] = None,
        packaging_type: Optional[str] = None,
        app_config: Optional[Dict[str, Any]] = None,
    ):
        self.id = f"bun_{get_xid()}"
        self.name = name
        self.created_by = created_by
        self.model_artifact_ids = model_artifact_ids
        self.schema_location = schema_location
        self.owner = owner
        self.bundle_metadata = bundle_metadata
        self.flavor = flavor

        # Artifact fields
        self.artifact_requirements = artifact_requirements
        self.artifact_location = artifact_location
        self.artifact_app_config = artifact_app_config
        self.artifact_framework_type = artifact_framework_type
        self.artifact_pytorch_image_tag = artifact_pytorch_image_tag
        self.artifact_tensorflow_version = artifact_tensorflow_version
        self.artifact_image_repository = artifact_image_repository
        self.artifact_image_tag = artifact_image_tag

        # Cloudpickle Artifact fields
        self.cloudpickle_artifact_load_predict_fn = cloudpickle_artifact_load_predict_fn
        self.cloudpickle_artifact_load_model_fn = cloudpickle_artifact_load_model_fn

        # Zip Artifact fields
        self.zip_artifact_load_predict_fn_module_path = zip_artifact_load_predict_fn_module_path
        self.zip_artifact_load_model_fn_module_path = zip_artifact_load_model_fn_module_path

        # Runnable Image fields
        self.runnable_image_repository = runnable_image_repository
        self.runnable_image_tag = runnable_image_tag
        self.runnable_image_command = runnable_image_command
        self.runnable_image_predict_route = runnable_image_predict_route
        self.runnable_image_healthcheck_route = runnable_image_healthcheck_route
        self.runnable_image_env = runnable_image_env
        self.runnable_image_protocol = runnable_image_protocol
        self.runnable_image_readiness_initial_delay_seconds = (
            runnable_image_readiness_initial_delay_seconds
        )

        # Streaming Enhanced Runnable Image fields
        self.streaming_enhanced_runnable_image_streaming_command = (
            streaming_enhanced_runnable_image_streaming_command
        )
        self.streaming_enhanced_runnable_image_streaming_predict_route = (
            streaming_enhanced_runnable_image_streaming_predict_route
        )

        # Triton Enhanced Runnable Image fields
        self.triton_enhanced_runnable_image_model_repository = (
            triton_enhanced_runnable_image_model_repository
        )
        self.triton_enhanced_runnable_image_model_replicas = (
            triton_enhanced_runnable_image_model_replicas
        )
        self.triton_enhanced_runnable_image_num_cpu = triton_enhanced_runnable_image_num_cpu
        self.triton_enhanced_runnable_image_commit_tag = triton_enhanced_runnable_image_commit_tag
        self.triton_enhanced_runnable_image_storage = triton_enhanced_runnable_image_storage
        self.triton_enhanced_runnable_image_memory = triton_enhanced_runnable_image_memory
        self.triton_enhanced_runnable_image_readiness_initial_delay_seconds = (
            triton_enhanced_runnable_image_readiness_initial_delay_seconds
        )

        # Legacy fields
        self.location = location
        self.version = version
        self.registered_model_name = registered_model_name
        self.requirements = requirements
        self.env_params = env_params
        self.packaging_type = packaging_type
        self.app_config = app_config

    @classmethod
    async def create(cls, session: AsyncSession, bundle: "Bundle") -> None:
        session.add(bundle)
        await session.commit()

    @classmethod
    async def select_by_name_created_by(
        cls, session: AsyncSession, name: str, created_by: str
    ) -> Optional["Bundle"]:
        bundles = select(Bundle).filter_by(name=name, created_by=created_by)
        bundle = await session.execute(bundles.order_by(Bundle.created_at.desc()).limit(1))
        return bundle.scalar_one_or_none()

    @classmethod
    async def select_by_name_owner(
        cls, session: AsyncSession, name: str, owner: str
    ) -> Optional["Bundle"]:
        bundles = select(Bundle).filter_by(name=name, owner=owner)
        bundle = await session.execute(bundles.order_by(Bundle.created_at.desc()).limit(1))
        return bundle.scalar_one_or_none()

    @classmethod
    async def select_all_by_name_created_by(
        cls, session: AsyncSession, name: str, created_by: str
    ) -> List["Bundle"]:
        bundles = await session.execute(select(Bundle).filter_by(name=name, created_by=created_by))
        return bundles.scalars().all()

    @classmethod
    async def select_all_by_name_owner(
        cls, session: AsyncSession, name: str, owner: str
    ) -> List["Bundle"]:
        bundles = await session.execute(select(Bundle).filter_by(name=name, owner=owner))
        return bundles.scalars().all()

    @classmethod
    async def select_by_id(cls, session: AsyncSession, bundle_id: str) -> Optional["Bundle"]:
        bundle = await session.execute(select(Bundle).filter_by(id=bundle_id))
        return bundle.scalar_one_or_none()

    @classmethod
    async def select_all_by_created_by(
        cls, session: AsyncSession, created_by: str
    ) -> List["Bundle"]:
        bundles = await session.execute(select(Bundle).filter_by(created_by=created_by))
        return bundles.scalars().all()

    @classmethod
    async def select_all_by_owner(cls, session: AsyncSession, owner: str) -> List["Bundle"]:
        bundles = await session.execute(select(Bundle).filter_by(owner=owner))
        return bundles.scalars().all()

    @classmethod
    async def select_all_by_filters_created_by(
        cls, session: AsyncSession, filters: List[Any], created_by: str
    ) -> List["Bundle"]:
        query = select(Bundle).filter_by(created_by=created_by)

        for f in filters:
            query = query.filter(f)

        bundles = await session.execute(query)
        return bundles.scalars().all()

    @classmethod
    async def select_all_by_filters_owner(
        cls, session: AsyncSession, filters: List[Any], owner: str
    ) -> List["Bundle"]:
        query = select(Bundle).filter_by(owner=owner)

        for f in filters:
            query = query.filter(f)

        bundles = await session.execute(query)
        return bundles.scalars().all()

    @classmethod
    async def delete(cls, session: AsyncSession, bundle: "Bundle") -> None:
        await session.delete(bundle)
        await session.commit()

    @classmethod
    async def duplicate_with_new_field_created_by(
        cls,
        session: AsyncSession,
        existing_bundle_name: str,
        created_by: str,
        new_kwargs: Dict[str, Any],
    ) -> None:
        existing_bundle = await Bundle.select_by_name_created_by(
            session, existing_bundle_name, created_by
        )
        if existing_bundle is None:
            return None

        bundle_args = {
            c.name: getattr(existing_bundle, c.name) for c in existing_bundle.__table__.columns
        }
        updated_kwargs = {**bundle_args, **new_kwargs}
        for key in AUTOGENERATED_FIELDS:
            updated_kwargs.pop(key)
        updated_bundle = Bundle(**updated_kwargs)
        return await Bundle.create(session, updated_bundle)

    @classmethod
    async def duplicate_with_new_field_owner(
        cls,
        session: AsyncSession,
        existing_bundle_name: str,
        owner: str,
        new_kwargs: Dict[str, Any],
    ) -> None:
        existing_bundle = await Bundle.select_by_name_owner(session, existing_bundle_name, owner)
        if existing_bundle is None:
            return None

        bundle_args = {
            c.name: getattr(existing_bundle, c.name) for c in existing_bundle.__table__.columns
        }
        updated_kwargs = {**bundle_args, **new_kwargs}
        for key in AUTOGENERATED_FIELDS:
            updated_kwargs.pop(key)
        updated_bundle = Bundle(**updated_kwargs)
        return await Bundle.create(session, updated_bundle)


class Endpoint(Base):
    __tablename__ = "endpoints"
    __table_args__ = (
        UniqueConstraint("name", "created_by", name="endpoint_name_created_by_uc"),
        UniqueConstraint("name", "owner", name="endpoint_name_owner_uc"),
        Index(  # Endpoint name is unique for LLMs
            "endpoint_name_llm_uc",
            "name",
            unique=True,
            postgresql_where=text("endpoint_metadata ? '_llm'"),
        ),
        {"schema": "llm_engine"},
    )

    id = Column(Text, primary_key=True)
    name = Column(Text, index=True)
    created_by = Column(String(SHORT_STRING), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=time_now)
    current_bundle_id = Column(Text, ForeignKey("llm_engine.bundles.id"))
    endpoint_metadata = Column(JSONB, default={})
    creation_task_id = Column(Text)
    endpoint_type = Column(Text, default="async")
    destination = Column(Text)
    # We set endpoint_status to READY as a default for backwards compatibility reasons
    # Endpoints should eventually end up as READY barring any bugs.
    # EndpointStatus.ready.value
    endpoint_status = Column(Text, default="READY")
    current_bundle = relationship("Bundle")
    owner = Column(String(SHORT_STRING))
    public_inference = Column(Boolean, default=False)

    def __init__(
        self,
        *,
        name: Optional[str] = None,
        created_by: Optional[str] = None,
        current_bundle_id: Optional[str] = None,
        endpoint_metadata: Optional[Dict[str, Any]] = None,
        creation_task_id: Optional[str] = None,
        endpoint_type: str = "async",
        destination: Optional[str] = None,
        endpoint_status: Optional[str] = "READY",  # EndpointStatus.ready.value
        owner: Optional[str] = None,
        public_inference: Optional[bool] = False,
    ):
        self.id = f"end_{get_xid()}"
        self.name = name
        self.created_by = created_by
        self.current_bundle_id = current_bundle_id
        self.endpoint_metadata = endpoint_metadata
        self.creation_task_id = creation_task_id
        self.endpoint_type = endpoint_type
        self.destination = destination
        self.endpoint_status = endpoint_status
        self.owner = owner
        self.public_inference = public_inference

    @classmethod
    async def create(cls, session: AsyncSession, endpoint: "Endpoint") -> None:
        session.add(endpoint)
        await session.commit()

    @classmethod
    async def update_by_name_created_by(
        cls, session: AsyncSession, name: str, created_by: str, kwargs: Dict[str, Any]
    ) -> None:
        stmt = (
            update(Endpoint)
            .where(Endpoint.name == name, Endpoint.created_by == created_by)
            .values(**kwargs)
        )

        await session.execute(stmt)
        await session.commit()

    @classmethod
    async def update_by_name_owner(
        cls, session: AsyncSession, name: str, owner: str, kwargs: Dict[str, Any]
    ) -> None:
        stmt = (
            update(Endpoint).where(Endpoint.name == name, Endpoint.owner == owner).values(**kwargs)
        )

        await session.execute(stmt)
        await session.commit()

    @classmethod
    async def update_endpoint_status(
        cls, session: AsyncSession, name: str, created_by: str, endpoint_status: str
    ) -> None:
        await cls.update_by_name_created_by(
            session, name, created_by, kwargs=dict(endpoint_status=endpoint_status)
        )

    # Select functions return the entire row, which is not necessarily optimal
    @classmethod
    async def select_by_name_created_by(
        cls, session: AsyncSession, name: str, created_by: str
    ) -> Optional["Endpoint"]:
        # TODO probably need a UC on owner, name also
        endpoint = await session.execute(
            select(Endpoint)
            .filter_by(name=name, created_by=created_by)
            .options(selectinload(Endpoint.current_bundle))
        )
        return endpoint.scalar_one_or_none()

    @classmethod
    async def select_all_by_created_by(
        cls, session: AsyncSession, created_by: str
    ) -> List["Endpoint"]:
        endpoints = await session.execute(
            select(Endpoint)
            .filter_by(created_by=created_by)
            .options(selectinload(Endpoint.current_bundle))
        )
        return endpoints.scalars().all()

    @classmethod
    async def select_all_by_owner(cls, session: AsyncSession, owner: str) -> List["Endpoint"]:
        endpoints = await session.execute(
            select(Endpoint).filter_by(owner=owner).options(selectinload(Endpoint.current_bundle))
        )
        return endpoints.scalars().all()

    @classmethod
    async def select_all_by_bundle_created_by(
        cls, session: AsyncSession, current_bundle_id: str, created_by: str
    ) -> List["Endpoint"]:
        endpoints = await session.execute(
            select(Endpoint)
            .filter_by(current_bundle_id=current_bundle_id, created_by=created_by)
            .options(selectinload(Endpoint.current_bundle))
        )
        return endpoints.scalars().all()

    @classmethod
    async def select_all_by_bundle_owner(
        cls, session: AsyncSession, current_bundle_id: str, owner: str
    ) -> List["Endpoint"]:
        endpoints = await session.execute(
            select(Endpoint)
            .filter_by(current_bundle_id=current_bundle_id, owner=owner)
            .options(selectinload(Endpoint.current_bundle))
        )
        return endpoints.scalars().all()

    @classmethod
    async def select_all_by_filters_created_by(
        cls, session: AsyncSession, filters: List[Any], created_by: str
    ) -> List["Endpoint"]:
        filters = [*filters, Endpoint.created_by == created_by]
        return await cls._select_all_by_filters(session, filters)

    @classmethod
    async def select_all_by_filters_owner(
        cls, session: AsyncSession, filters: List[Any], owner: str
    ) -> List["Endpoint"]:
        filters = [*filters, Endpoint.owner == owner]
        return await cls._select_all_by_filters(session, filters)

    @classmethod
    async def select_by_id(cls, session: AsyncSession, endpoint_id: str) -> Optional["Endpoint"]:
        endpoint = await session.execute(
            select(Endpoint)
            .filter_by(id=endpoint_id)
            .options(selectinload(Endpoint.current_bundle))
        )
        return endpoint.scalar_one_or_none()

    @classmethod
    async def _select_all_by_filters(
        cls,
        session: AsyncSession,
        filters: List[Any],
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List["Endpoint"]:
        """DO NOT USE FOR EXTERNAL FUNCTIONS, this bypasses the owner
        check and should only be used for internal use cases"""
        query = select(Endpoint).options(selectinload(Endpoint.current_bundle))

        for f in filters:
            query = query.filter(f)
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)

        endpoints = await session.execute(query)
        return endpoints.scalars().all()

    @classmethod
    async def delete(cls, session: AsyncSession, endpoint: "Endpoint") -> None:
        await session.delete(endpoint)
        await session.commit()


class BatchJob(Base):
    __tablename__ = "batch_jobs"
    __table_args__ = ({"schema": "llm_engine"},)

    id = Column(Text, primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    batch_job_status = Column(Text, name="status", nullable=False)
    created_by = Column(String(SHORT_STRING), index=True, nullable=False)
    owner = Column(String(SHORT_STRING), index=True, nullable=False)
    model_bundle_id = Column(
        Text, ForeignKey("llm_engine.bundles.id", ondelete="SET NULL"), nullable=False
    )
    model_endpoint_id = Column(Text, ForeignKey("llm_engine.endpoints.id"), nullable=True)
    task_ids_location = Column(Text, nullable=True)
    result_location = Column(Text, nullable=True)

    model_bundle = relationship("Bundle")

    def __init__(
        self,
        *,
        batch_job_status: Optional[str] = None,
        created_by: Optional[str] = None,
        owner: Optional[str] = None,
        model_bundle_id: Optional[str] = None,
        model_endpoint_id: Optional[str] = None,
        task_ids_location: Optional[str] = None,
        result_location: Optional[str] = None,
    ):
        self.id = f"bat_{get_xid()}"
        self.batch_job_status = batch_job_status
        self.created_by = created_by
        self.owner = owner
        self.model_bundle_id = model_bundle_id
        self.model_endpoint_id = model_endpoint_id
        self.task_ids_location = task_ids_location
        self.result_location = result_location

    @classmethod
    async def create(cls, session: AsyncSession, batch_job: "BatchJob") -> None:
        session.add(batch_job)
        await session.commit()

    @classmethod
    async def select_all_by_owner(cls, session: AsyncSession, owner: str) -> List["BatchJob"]:
        batch_jobs = await session.execute(
            select(BatchJob).filter_by(owner=owner).options(selectinload(BatchJob.model_bundle))
        )
        return batch_jobs.scalars().all()

    @classmethod
    async def select_all_by_bundle_owner(
        cls, session: AsyncSession, model_bundle_id: str, owner: str
    ) -> List["BatchJob"]:
        batch_jobs = await session.execute(
            select(BatchJob)
            .filter_by(model_bundle_id=model_bundle_id, owner=owner)
            .options(selectinload(BatchJob.model_bundle))
        )
        return batch_jobs.scalars().all()

    @classmethod
    async def select_by_id(cls, session: AsyncSession, batch_job_id: str) -> Optional["BatchJob"]:
        batch_job = await session.execute(
            select(BatchJob).filter_by(id=batch_job_id).options(selectinload(BatchJob.model_bundle))
        )
        return batch_job.scalar_one_or_none()

    @classmethod
    async def update_by_id(
        cls, session: AsyncSession, batch_job_id: str, kwargs: Dict[str, Any]
    ) -> None:
        update_kwargs = kwargs.copy()
        if "status" in kwargs:
            update_kwargs["batch_job_status"] = update_kwargs.pop("status")
        stmt = update(BatchJob).where(BatchJob.id == batch_job_id).values(**update_kwargs)
        await session.execute(stmt)
        await session.commit()


class DockerImageBatchJobBundle(Base):
    __tablename__ = "docker_image_batch_job_bundles"
    __table_args__ = ({"schema": "llm_engine"},)

    id = Column("id", Text, primary_key=True)
    name = Column("name", Text, nullable=False)
    created_by = Column("created_by", String(SHORT_STRING), index=True, nullable=False)
    created_at = Column(
        "created_at", DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    owner = Column("owner", String(SHORT_STRING), index=True, nullable=False)
    image_repository = Column("image_repository", Text, nullable=False)
    image_tag = Column("image_tag", Text, nullable=False)
    command = Column("command", ARRAY(Text), nullable=False)
    env = Column("env", JSON, nullable=False)
    mount_location = Column("mount_location", Text, nullable=True)
    cpus = Column("cpus", Text, nullable=True)
    memory = Column("memory", Text, nullable=True)
    storage = Column("storage", Text, nullable=True)
    gpus = Column("gpus", Integer, nullable=True)
    gpu_type = Column("gpu_type", Text, nullable=True)
    public = Column("public", Boolean, nullable=True)

    def __init__(
        self,
        *,
        name: str,
        created_by: str,
        owner: str,
        image_repository: str,
        image_tag: str,
        command: List[str],
        env: Dict[str, str],
        mount_location: Optional[str],
        cpus: Optional[str],
        memory: Optional[str],
        storage: Optional[str],
        gpus: Optional[str],
        gpu_type: Optional[str],
        public: Optional[bool] = False,
    ):
        self.id = f"batbun_{get_xid()}"
        self.name = name
        self.created_by = created_by
        self.owner = owner
        self.image_repository = image_repository
        self.image_tag = image_tag
        self.command = command
        self.env = env
        self.mount_location = mount_location
        self.cpus = cpus
        self.memory = memory
        self.storage = storage
        self.gpus = gpus
        self.gpu_type = gpu_type
        self.public = public

    @classmethod
    async def create(cls, session: AsyncSession, batch_bundle: "DockerImageBatchJobBundle") -> None:
        session.add(batch_bundle)
        await session.commit()

    @classmethod
    async def select_all_by_owner(
        cls, session: AsyncSession, owner: str
    ) -> List["DockerImageBatchJobBundle"]:
        batch_bundles = await session.execute(
            select(DockerImageBatchJobBundle).filter_by(owner=owner)
        )
        return batch_bundles.scalars().all()

    @classmethod
    async def select_latest_by_name_owner(
        cls, session: AsyncSession, name: str, owner: str
    ) -> Optional["DockerImageBatchJobBundle"]:
        batch_bundles = select(DockerImageBatchJobBundle).filter_by(name=name, owner=owner)
        batch_bundle = await session.execute(
            batch_bundles.order_by(DockerImageBatchJobBundle.created_at.desc()).limit(1)
        )
        return batch_bundle.scalar_one_or_none()

    @classmethod
    async def select_all_by_name_owner(
        cls, session: AsyncSession, name: str, owner: str
    ) -> List["DockerImageBatchJobBundle"]:
        batch_bundles = await session.execute(
            select(DockerImageBatchJobBundle).filter_by(name=name, owner=owner)
        )
        return batch_bundles.scalars().all()

    @classmethod
    async def select_by_id(
        cls, session: AsyncSession, batch_bundle_id: str
    ) -> Optional["DockerImageBatchJobBundle"]:
        batch_bundle = await session.execute(
            select(DockerImageBatchJobBundle).filter_by(id=batch_bundle_id)
        )
        return batch_bundle.scalar_one_or_none()


class Trigger(Base):
    __tablename__ = "triggers"
    __table_args__ = (
        UniqueConstraint("name", "owner", name="uq_triggers_name_owner"),
        {"schema": "llm_engine"},
    )

    id = Column("id", String, nullable=False, primary_key=True)
    name = Column("name", String, nullable=False)
    owner = Column("owner", String, nullable=False)
    created_by = Column("created_by", String, nullable=False)
    created_at = Column(
        "created_at", DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    cron_schedule = Column("cron_schedule", String, nullable=False)
    docker_image_batch_job_bundle_id = Column(
        "docker_image_batch_job_bundle_id",
        String,
        ForeignKey("llm_engine.docker_image_batch_job_bundles.id"),
        nullable=False,
    )
    default_job_config = Column("default_job_config", JSONB, nullable=True)
    default_job_metadata = Column("default_job_metadata", JSONB, nullable=True)

    def __init__(
        self,
        *,
        name: str,
        owner: str,
        created_by: str,
        cron_schedule: str,
        docker_image_batch_job_bundle_id: str,
        default_job_config: Optional[Dict[str, Any]] = None,
        default_job_metadata: Optional[Dict[str, str]] = None,
    ):
        self.id = f"trig_{get_xid()}"
        self.name = name
        self.owner = owner
        self.created_by = created_by
        self.cron_schedule = cron_schedule
        self.docker_image_batch_job_bundle_id = docker_image_batch_job_bundle_id
        self.default_job_config = default_job_config
        self.default_job_metadata = default_job_metadata