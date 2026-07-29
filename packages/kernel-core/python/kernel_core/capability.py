"""
bOPEN Capability & Module Registry Engine v1.0 (WP-P3-03 / BOPEN-MOD-001).

Governs global module catalog lifecycle (registered -> validated -> approved -> available)
and tenant-specific capability resolution bound to validated active context.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Union, Any
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


class StructurallyInvalidContextError(Exception):
    pass


@dataclass(frozen=True)
class ModuleDependency:
    module_id: str
    version_constraint: str = ">=1.0.0"

    @classmethod
    def from_item(cls, item: Union[str, dict, ModuleDependency]) -> ModuleDependency:
        if isinstance(item, ModuleDependency):
            return item
        elif isinstance(item, str):
            return cls(module_id=item)
        elif isinstance(item, dict):
            if "module_id" not in item:
                raise InvalidModuleManifestError("Dependency dict missing 'module_id'")
            return cls(module_id=item["module_id"], version_constraint=item.get("version_constraint", ">=1.0.0"))
        raise InvalidModuleManifestError(f"Invalid dependency specification: {item}")


@dataclass(frozen=True)
class ModuleManifest:
    module_id: str
    name: str
    version: str
    min_platform_version: str
    capabilities: Tuple[str, ...]
    resources: Tuple[str, ...]
    dependencies: Tuple[ModuleDependency, ...] = ()
    status: ModuleStatus = ModuleStatus.REGISTERED

    @classmethod
    def from_dict(cls, data: dict) -> ModuleManifest:
        for field_name in ["module_id", "name", "version", "min_platform_version", "capabilities", "resources"]:
            if field_name not in data:
                raise InvalidModuleManifestError(f"Missing required field: {field_name}")

        deps = []
        for dep in data.get("dependencies", []):
            deps.append(ModuleDependency.from_item(dep))

        return cls(
            module_id=data["module_id"],
            name=data["name"],
            version=data["version"],
            min_platform_version=data["min_platform_version"],
            capabilities=tuple(data["capabilities"]),
            resources=tuple(data["resources"]),
            dependencies=tuple(deps),
            status=ModuleStatus(data.get("status", ModuleStatus.REGISTERED.value))
        )


class ModuleRegistry:
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

        # Cycle detection and dependency resolution
        visited = set()
        stack = set()

        def resolve_deps(curr_id: str):
            if curr_id in stack:
                raise DependencyResolutionError(f"Cyclic dependency detected involving module {curr_id}")
            if curr_id in visited:
                return
            stack.add(curr_id)
            if curr_id not in self._modules:
                raise DependencyResolutionError(f"Prerequisite module {curr_id} missing")
            curr_manifest = self._modules[curr_id]
            for dep in curr_manifest.dependencies:
                resolve_deps(dep.module_id)
            stack.remove(curr_id)
            visited.add(curr_id)

        for dep in manifest.dependencies:
            resolve_deps(dep.module_id)

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

    def publish_module(self, module_id: str) -> ModuleManifest:
        if module_id not in self._modules or self._modules[module_id].status != ModuleStatus.APPROVED:
            raise InvalidModuleManifestError(f"Module {module_id} must be approved before publication")
        published = ModuleManifest(
            module_id=self._modules[module_id].module_id,
            name=self._modules[module_id].name,
            version=self._modules[module_id].version,
            min_platform_version=self._modules[module_id].min_platform_version,
            capabilities=self._modules[module_id].capabilities,
            resources=self._modules[module_id].resources,
            dependencies=self._modules[module_id].dependencies,
            status=ModuleStatus.AVAILABLE
        )
        self._modules[module_id] = published
        return published

    def is_available(self, module_id: str) -> bool:
        manifest = self._modules.get(module_id)
        return manifest is not None and manifest.status == ModuleStatus.AVAILABLE

    def get_tenant_capabilities(self, context: ContextPayload, module_id: str) -> List[str]:
        # Strict context structural validation (INV-P3-001)
        if not context.context_id or not context.principal_id or not context.tenant_id or not context.active_membership_id:
            raise StructurallyInvalidContextError("ContextPayload is missing required context_id, principal_id, tenant_id, or active_membership_id")

        manifest = self._modules.get(module_id)
        if not manifest or manifest.status != ModuleStatus.AVAILABLE:
            return []
        return list(manifest.capabilities)


class CapabilityResolver:
    def __init__(self, module_registry: ModuleRegistry):
        self._registry = module_registry

    def resolve_capability(self, capability_id: str) -> str:
        if capability_id not in self._registry._capabilities:
            raise CapabilityNotFoundError(f"Capability {capability_id} not registered in platform catalog")
        return self._registry._capabilities[capability_id]


# Backwards compatibility aliases
CapabilityRegistry = ModuleRegistry
