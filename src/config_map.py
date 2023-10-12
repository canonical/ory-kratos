# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""A helper class for managing the configMaps holding the kratos config."""

import logging
from typing import Dict

from lightkube import ApiError, Client
from lightkube.models.meta_v1 import ObjectMeta
from lightkube.resources.core_v1 import ConfigMap
from ops.charm import CharmBase

logger = logging.getLogger(__name__)


class ConfigMapManager:
    """A helper class for managing configMaps."""

    configmaps = {}

    @classmethod
    def create_all(cls) -> None:
        """Create all the configMaps."""
        for cm in cls.configmaps.values():
            cm.create()

    @classmethod
    def delete_all(cls) -> None:
        """Delete all the configMaps."""
        for cm in cls.configmaps.values():
            cm.delete()

    @classmethod
    def register(cls, cm: "ConfigMapBase") -> None:
        """Register a configMap."""
        cls.configmaps[f"{cm.namespace}_{cm.name}"] = cm


class ConfigMapBase:
    """Base class for managing a configMap."""

    def __init__(self, configmap_name: str, client: Client, charm: CharmBase) -> None:
        self.name = configmap_name
        self._client = client
        self._charm = charm
        ConfigMapManager.register(self)

    @property
    def namespace(self):
        """The namespace of the ConfigMap."""
        return self._charm.model.name

    def create(self):
        """Create the configMap."""
        try:
            self._client.get(ConfigMap, self.name, namespace=self.namespace)
            return
        except ApiError:
            pass

        cm = ConfigMap(
            apiVersion="v1",
            kind="ConfigMap",
            # TODO @nsklikas: revisit labels
            metadata=ObjectMeta(
                name=self.name,
                namespace=self.namespace,
                labels={
                    "juju-app-name": self._charm.app.name,
                    "app.kubernetes.io/managed-by": "juju",
                },
            ),
        )
        self._client.create(cm)

    def update(self, data: Dict):
        """Update the configMap."""
        try:
            cm = self._client.get(ConfigMap, self.name, namespace=self.namespace)
        except ApiError:
            return
        cm.data = data
        self._client.replace(cm)

    def get(self):
        """Get the configMap."""
        try:
            cm = self._client.get(ConfigMap, self.name, namespace=self.namespace)
        except ApiError:
            return {}
        return cm.data

    def delete(self):
        """Delete the configMap."""
        try:
            self._client.delete(ConfigMap, self.name, namespace=self.namespace)
        except ApiError:
            raise ValueError


class KratosConfigMap(ConfigMapBase):
    """Class for managing the Kratos config configMap."""

    def __init__(self, client: Client, charm: CharmBase) -> None:
        super().__init__("kratos-config", client, charm)


class IdentitySchemaConfigMap(ConfigMapBase):
    """Class for managing the Identity Schemas configMap."""

    def __init__(self, client: Client, charm: CharmBase) -> None:
        super().__init__("identity-schemas", client, charm)


class ProvidersConfigMap(ConfigMapBase):
    """Class for managing the Providers configMap."""

    def __init__(self, client: Client, charm: CharmBase) -> None:
        super().__init__("providers", client, charm)


def create_all():
    """Create all the register configMaps."""
    ConfigMapManager.create_all()


def delete_all():
    """Delete all the register configMaps."""
    ConfigMapManager.delete_all()
