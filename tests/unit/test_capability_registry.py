"""
Phase 3 Unit Acceptance Suite — Capability & Module Registry (BOPEN-MOD-001 / WP-P3-02 & WP-P3-03).

Verifies capability registration, module manifest validation, dependency resolution,
cyclic dependency rejection, schema contract compliance, and global catalog vs tenant context lifecycle rules.
"""

import unittest
from pathlib import Path
import json

from kernel_core.types import ContextPayload

# Capability & Module Registry imports
from kernel_core.capability import (
    ModuleRegistry,
    CapabilityResolver,
    ModuleManifest,
    CapabilityStatus,
    ModuleStatus,
    InvalidModuleManifestError,
    CapabilityNotFoundError,
    DependencyResolutionError,
    StructurallyInvalidContextError,
)

ROOT = Path(__file__).resolve().parents[2]


class CapabilityRegistryUnitTests(unittest.TestCase):
    def setUp(self):
        self.registry = ModuleRegistry()
        self.resolver = CapabilityResolver(self.registry)
        self.valid_manifest_data = {
            "module_id": "mod_practice_mgmt",
            "name": "Practice Management",
            "version": "1.0.0",
            "min_platform_version": "1.0.0",
            "capabilities": ["cap_invoice_create", "cap_invoice_read"],
            "resources": ["res_invoice"],
            "dependencies": []
        }
        self.valid_context = ContextPayload(
            context_id="ctx_123",
            principal_id="usr_alice",
            tenant_id="tnt_alpha",
            active_membership_id="mem_alice_alpha",
            roles=["member"]
        )

    def test_register_module_manifest_success(self):
        manifest = ModuleManifest.from_dict(self.valid_manifest_data)
        registered = self.registry.register_module(manifest)
        self.assertEqual(registered.status, ModuleStatus.REGISTERED)
        self.assertEqual(registered.module_id, "mod_practice_mgmt")

    def test_validate_approve_and_publish_module_lifecycle(self):
        manifest = ModuleManifest.from_dict(self.valid_manifest_data)
        self.registry.register_module(manifest)

        # Must be validated first
        validated = self.registry.validate_module("mod_practice_mgmt")
        self.assertEqual(validated.status, ModuleStatus.VALIDATED)

        # Must be approved second
        approved = self.registry.approve_module("mod_practice_mgmt")
        self.assertEqual(approved.status, ModuleStatus.APPROVED)

        # APPROVED is not yet AVAILABLE (INV-MOD-002)
        self.assertFalse(self.registry.is_available("mod_practice_mgmt"))
        self.assertEqual(self.registry.get_tenant_capabilities(self.valid_context, "mod_practice_mgmt"), [])

        # Must be published to become AVAILABLE
        published = self.registry.publish_module("mod_practice_mgmt")
        self.assertEqual(published.status, ModuleStatus.AVAILABLE)
        self.assertTrue(self.registry.is_available("mod_practice_mgmt"))
        self.assertEqual(self.registry.get_tenant_capabilities(self.valid_context, "mod_practice_mgmt"), ["cap_invoice_create", "cap_invoice_read"])

    def test_unregistered_capability_lookup_fails_closed(self):
        with self.assertRaises(CapabilityNotFoundError):
            self.resolver.resolve_capability("cap_unregistered")

    def test_dict_and_string_dependency_parsing(self):
        manifest_data = {
            "module_id": "mod_leasing",
            "name": "Leasing",
            "version": "1.0.0",
            "min_platform_version": "1.0.0",
            "capabilities": ["cap_lease_create"],
            "resources": ["res_lease"],
            "dependencies": [
                {"module_id": "mod_practice_mgmt", "version_constraint": ">=1.0.0"}
            ]
        }
        manifest = ModuleManifest.from_dict(manifest_data)
        self.assertEqual(manifest.dependencies[0].module_id, "mod_practice_mgmt")

    def test_missing_dependency_fails_resolution(self):
        dependent_manifest_data = {
            "module_id": "mod_analytics",
            "name": "Analytics",
            "version": "1.0.0",
            "min_platform_version": "1.0.0",
            "capabilities": ["cap_analytics_export"],
            "resources": ["res_analytics"],
            "dependencies": ["mod_nonexistent"]
        }
        manifest = ModuleManifest.from_dict(dependent_manifest_data)
        self.registry.register_module(manifest)
        with self.assertRaises(DependencyResolutionError):
            self.registry.validate_module("mod_analytics")

    def test_cyclic_dependency_rejected(self):
        mod_a = ModuleManifest.from_dict({
            "module_id": "mod_a", "name": "A", "version": "1.0.0", "min_platform_version": "1.0.0",
            "capabilities": ["cap_a"], "resources": ["res_a"], "dependencies": ["mod_b"]
        })
        mod_b = ModuleManifest.from_dict({
            "module_id": "mod_b", "name": "B", "version": "1.0.0", "min_platform_version": "1.0.0",
            "capabilities": ["cap_b"], "resources": ["res_b"], "dependencies": ["mod_a"]
        })
        self.registry.register_module(mod_a)
        self.registry.register_module(mod_b)
        with self.assertRaises(DependencyResolutionError):
            self.registry.validate_module("mod_a")

    def test_structurally_invalid_context_fails_closed(self):
        manifest = ModuleManifest.from_dict(self.valid_manifest_data)
        self.registry.register_module(manifest)
        self.registry.validate_module("mod_practice_mgmt")
        self.registry.approve_module("mod_practice_mgmt")
        self.registry.publish_module("mod_practice_mgmt")

        # Blank tenant_id, principal_id or context_id fails closed (INV-P3-001)
        invalid_contexts = [
            ContextPayload(context_id="", principal_id="usr_a", tenant_id="tnt_a", active_membership_id="mem_a", roles=[]),
            ContextPayload(context_id="ctx_1", principal_id="", tenant_id="tnt_a", active_membership_id="mem_a", roles=[]),
            ContextPayload(context_id="ctx_1", principal_id="usr_a", tenant_id="", active_membership_id="mem_a", roles=[]),
            ContextPayload(context_id="ctx_1", principal_id="usr_a", tenant_id="tnt_a", active_membership_id="", roles=[]),
        ]
        for ctx in invalid_contexts:
            with self.assertRaises(StructurallyInvalidContextError):
                self.registry.get_tenant_capabilities(ctx, "mod_practice_mgmt")


if __name__ == "__main__":
    unittest.main()
