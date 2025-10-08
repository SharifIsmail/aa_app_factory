#!/usr/bin/env python3
import argparse
import sys

from kubernetes import client
from kubernetes import config as k8s_config
from kubernetes.client.exceptions import ApiException
from loguru import logger

from deployment.deploy_settings import DeploySettings

ALLOWED_USECASES_ANNOTATION: dict[str, str] = {
    "os.pharia.ai/allowed-usecases": '["Supplier Briefing"]'
}


class VertexSecretManager:
    """Manage the Kubernetes secret for Vertex AI credentials."""

    def __init__(self) -> None:
        """Initialize the secret manager."""
        self.deploy_settings = DeploySettings()  # type: ignore
        self._load_kube_config()
        self.core_v1_api_client = client.CoreV1Api()

        self.kubeconfig_path = self.deploy_settings.kubeconfig_path
        self.vertex_credentials = (
            self.deploy_settings.vertex_ai_credentials.get_secret_value()
        )
        self.secret_name = self.deploy_settings.vertex_secret_name
        self.namespace = self.deploy_settings.kubernetes_namespace

    def _load_kube_config(self) -> None:
        """Load Kubernetes configuration from the specified kubeconfig file."""
        kubeconfig_file = self.deploy_settings.kubeconfig_path

        if not kubeconfig_file.exists():
            logger.error(f"Error: Kubeconfig file not found at {kubeconfig_file}")
            sys.exit(1)

        try:
            k8s_config.kube_config.load_kube_config(config_file=str(kubeconfig_file))
            logger.info(f"Loaded kubeconfig from {kubeconfig_file}")
        except Exception as e:
            logger.error(f"Error loading kubeconfig: {e}")
            sys.exit(1)

    def create_secret(self) -> None:
        """Create the Kubernetes secret with Vertex AI credentials."""

        secret_metadata = client.V1ObjectMeta(
            name=self.secret_name,
            namespace=self.namespace,
            annotations=ALLOWED_USECASES_ANNOTATION,
        )

        secret_data = {
            "credentials": self.vertex_credentials,
        }

        secret = client.V1Secret(
            api_version="v1",
            kind="Secret",
            metadata=secret_metadata,
            type="Opaque",
            string_data=secret_data,
        )

        self.core_v1_api_client.create_namespaced_secret(
            namespace=self.namespace, body=secret
        )
        logger.info(
            f"✅ Successfully created secret '{self.secret_name}' in namespace '{self.namespace}'"
        )

    def update_secret(self) -> None:
        """Update an existing Kubernetes secret with new Vertex AI credentials."""
        secret_metadata = client.V1ObjectMeta(
            name=self.secret_name,
            namespace=self.namespace,
            annotations=ALLOWED_USECASES_ANNOTATION,
        )

        secret_data = {
            "credentials": self.vertex_credentials,
        }

        secret = client.V1Secret(
            api_version="v1",
            kind="Secret",
            metadata=secret_metadata,
            type="Opaque",
            string_data=secret_data,
        )

        self.core_v1_api_client.replace_namespaced_secret(
            name=self.secret_name, namespace=self.namespace, body=secret
        )
        logger.info(
            f"✅ Successfully updated secret '{self.secret_name}' in namespace '{self.namespace}'"
        )

    def delete_secret(self) -> None:
        """Delete the Kubernetes secret."""
        try:
            self.core_v1_api_client.delete_namespaced_secret(
                name=self.secret_name, namespace=self.namespace
            )
            logger.info(
                f"✅ Successfully deleted secret '{self.secret_name}' from namespace '{self.namespace}'"
            )
        except ApiException as e:
            if e.status == 404:
                logger.info(
                    f"⚠️  Secret '{self.secret_name}' not found in namespace '{self.namespace}'"
                )
            else:
                logger.info(f"Error deleting secret: {e}")
                sys.exit(1)

    def get_secret(self) -> None:
        """Get information about the Kubernetes secret."""
        try:
            secret = self.core_v1_api_client.read_namespaced_secret(
                name=self.secret_name, namespace=self.namespace
            )
            if secret.metadata:
                logger.info(f"Secret: {secret.metadata.name}")
                logger.info(f"Namespace: {secret.metadata.namespace}")
                logger.info(f"Type: {secret.type}")
                logger.info(f"Creation time: {secret.metadata.creation_timestamp}")
                if secret.metadata.annotations:
                    logger.info("Annotations:")
                    for key, value in secret.metadata.annotations.items():
                        logger.info(f"  {key}: {value}")
            if secret.data:
                logger.info(f"Data keys: {', '.join(secret.data.keys())}")
        except ApiException as e:
            if e.status == 404:
                logger.info(
                    f"⚠️  Secret '{self.secret_name}' not found in namespace '{self.namespace}'"
                )
            else:
                logger.info(f"Error getting secret: {e}")
                sys.exit(1)


def main() -> None:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Manage Kubernetes secret for Vertex AI credentials"
    )
    parser.add_argument(
        "command",
        choices=["create", "update", "delete", "get"],
        help="Command to execute",
    )

    args = parser.parse_args()

    manager = VertexSecretManager()

    if args.command == "create":
        manager.create_secret()
    elif args.command == "update":
        manager.update_secret()
    elif args.command == "delete":
        manager.delete_secret()
    elif args.command == "get":
        manager.get_secret()


if __name__ == "__main__":
    main()
