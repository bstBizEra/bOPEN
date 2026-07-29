"""
bOPEN Capability & Module Registry Engine v1.0 (WP-P3-03 / BOPEN-MOD-001).

Governs global module catalog lifecycle (registered -> validated -> approved -> available)
and tenant-specific capability resolution bound to validated active context.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set
from kernel_core.types import ContextPayload


class ModuleStatus(str, Enum):
    REGISTERED = "registered"
    VALIDATED = "validated"
    APPROVED = "approved"
    AVAILABLE = "available"
    DEPRECATED = "deprecated"


class CapabilityStatus(str, Enum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    REVOKED = "revoked"


class InvalidModuleManifestError(Exception):
    pass


class CapabilityNotFoundError(Exception):
    pass


class DependencyResolutionError(Exception):
    pass


@dataclass(frozen=True)
class ModuleManifest:
    module_id: str
    name: str
    version: str
    min_platform_version: str
    capabilities: Tuple[str, ...]
    resources: Tuple[str, ...]
    dependencies: Tuple[str, ...] = ()
    status: ModuleStatus = ModuleStatus.REGISTERED

    @classmethod
    def from_dict(cls, data: dict) -> ModuleManifest:
        for field_name in ["module_id", "name", "version", "min_platform_version", "capabilities", "resources"]:
            if field_name not in data:
                raise InvalidModuleManifestError(f"Missing required field: {field_name}")
        return cls(
            module_id=data["module_id"],
            name=data["name"],
            version=data["version"],
            min_platform_version=data["min_platform_version"],
            capabilities=tuple(data["capabilities"]),
            resources=tuple(data["resources"]),
            dependencies=tuple(data.get("dependencies", ())),
            status=ModuleStatus(data.get("status", ModuleStatus.REGISTERED.value))
        )


class CapabilityRegistry:
    def __init__(self):
        self._modules: Dict[str, ModuleManifest] = {}
        self._capabilities: Dict[str, str] = {}  # capability_id -> module_id

    def register_module(self, manifest: ModuleManifest) -> ModuleManifest:
        self._modules[manifest.module_id] = manifest
        for cap in manifest.capabilities:
            self._capabilities[cap] = manifest.module_id
        return manifest

    def validate_module(self, module_id: str) -> ModuleManifest:
        if module_id not in self._modules:
            raise InvalidModuleManifestError(f"Module {module_id} not registered")
        manifest = self._modules[module_id]
        
        # Check dependencies
        for dep_id in manifest.dependencies:
            if dep_id not in self._modules:
                raise DependencyResolutionError(f"Prerequisite module {dep_id} missing")
        
        validated = ModuleManifest(
            module_id=manifest.module_id,
            name=manifest.name,
            version=manifest.version,
            min_platform_version=manifest.min_platform_version,
            capabilities=manifest.capabilities,
            resources=manifest.resources,
            dependencies=manifest.dependencies,
            status=ModuleStatus.VALIDATED
        )
        self._modules[module_id] = validated
        return validated

    def approve_module(self, module_id: str) -> ModuleManifest:
        if module_id not in self._modules or self._modules[module_id].status != ModuleStatus.VALIDATED:
            raise InvalidModuleManifestError(f"Module {module_id} must be validated before approval")
        approved = ModuleManifest(
            module_id=self._modules[module_id].module_id,
            name=self._modules[module_id].name,
            version=self._modules[module_id].version,
            min_platform_version=self._modules[module_id].min_platform_version,
            capabilities=self._modules[module_id].capabilities,
            resources=self._modules[module_id].resources,
            dependencies=self._modules[module_id].dependencies,
            status=ModuleStatus.APPROVED
        )
        self._modules[module_id] = approved
        return approved

    def is_available(self, module_id: str) -> bool:
        manifest = self._modules.get(module_id)
        return manifest is not None and manifest.status in {ModuleStatus.APPROVED, ModuleStatus.AVAILABLE}

    def resolve_capability(self, capability_id: str) -> str:
        if capability_id not in self._capabilities:
            raise CapabilityNotFoundError(f"Capability {capability_id} not registered in platform catalog")
        return self._capabilities[capability_id]

    def get_tenant_capabilities(self, context: ContextPayload, module_id: str) -> List[str]:
        if not context.tenant_id:
            raise ValueError("Validated active context must specify a valid tenant_id")
        manifest = self._modules.get(module_id)
        if not manifest or manifest.status not in {ModuleStatus.APPROVED, ModuleStatus.AVAILABLE}:
            return []
        return list(manifest.capabilities)
