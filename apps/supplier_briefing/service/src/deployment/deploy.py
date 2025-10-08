#!/usr/bin/env python3
"""
Deployment script for supplier-briefing-no-chat service.
"""

import argparse
import json
import re
import sys

import requests

from deployment.deploy_settings import DeploySettings


class Deployer:
    def __init__(self, deploy_settings: DeploySettings) -> None:
        self.deploy_settings = deploy_settings
        self.pharia_api_os_usecases_base_url = (
            self.deploy_settings.pharia_api_os_usecases_base_url
        )
        self.headers = self.deploy_settings.pharia_auth_header

    @staticmethod
    def replace_env_vars(
        obj: dict | list | str, deploy_settings: DeploySettings
    ) -> dict | list | str:
        """Recursively replace environment variables in config object."""
        if isinstance(obj, str):
            # Replace ${VAR_NAME} with the actual environment variable value
            pattern = r"\$\{([^}]+)\}"

            def replacer(match: re.Match[str]) -> str:
                var_name = match.group(1)

                match var_name:
                    case "PHARIA_API_TOKEN":
                        return deploy_settings.pharia_api_token.get_secret_value()
                    case "VERTEX_SECRET_NAME":
                        return deploy_settings.vertex_secret_name
                    case _:
                        raise Exception(
                            f"Unexpected env variable to replace: {type(match)}"
                        )

            return re.sub(pattern, replacer, obj)
        elif isinstance(obj, dict):
            return {
                key: Deployer.replace_env_vars(value, deploy_settings)
                for key, value in obj.items()
            }
        elif isinstance(obj, list):
            return [Deployer.replace_env_vars(item, deploy_settings) for item in obj]
        else:
            return obj

    def list_usecases(self) -> None:
        try:
            response = requests.get(
                f"{self.pharia_api_os_usecases_base_url}", headers=self.headers
            )
            response.raise_for_status()

            data = response.json()
            usecases = data.get("data", [])

            if not usecases:
                print("No usecases found.")
                return

            print(f"\nFound {len(usecases)} usecase(s):")
            print("-" * 80)

            for usecase in usecases:
                name = usecase.get("name", "Unknown")
                usecase_id = usecase.get("id", "Unknown")
                description = usecase.get("description", "No description")
                created_at = usecase.get("created_at", "Unknown")

                deployment = usecase.get("deployment")
                if deployment:
                    status = deployment.get("status", "Unknown")
                    deployment_id = deployment.get("id", "Unknown")
                    status_emoji = (
                        "✅"
                        if status == "running"
                        else "❌"
                        if status == "failed"
                        else "⏳"
                    )
                    print(f"{status_emoji} {name} (ID: {usecase_id})")
                    print(f"    Description: {description}")
                    print(f"    Status: {status} (Deployment ID: {deployment_id})")
                    print(f"    Created: {created_at}")
                else:
                    print(f"❌ {name} (ID: {usecase_id}) - Not deployed")
                    print(f"    Description: {description}")
                    print(f"    Created: {created_at}")
                print()

        except requests.exceptions.RequestException as e:
            print(f"Error fetching usecases: {e}")
            sys.exit(1)

    def create_usecase(self, name: str, description: str) -> None:
        try:
            payload = {"name": name, "description": description}
            response = requests.post(
                self.pharia_api_os_usecases_base_url, headers=self.headers, json=payload
            )
            response.raise_for_status()

            data = response.json()
            usecase_id = data.get("id")
            print(f"Created usecase '{name}' with ID: {usecase_id}")

        except requests.exceptions.RequestException as e:
            print(f"Error creating usecase: {e}")
            sys.exit(1)

    def delete_usecase(self, usecase_id: str) -> None:
        try:
            response = requests.delete(
                f"{self.pharia_api_os_usecases_base_url}/{usecase_id}",
                headers=self.headers,
            )

            if response.status_code == 204:
                print(f"Successfully deleted usecase {usecase_id}")
            elif response.status_code == 422:
                print(
                    f"Error: Usecase {usecase_id} cannot be deleted (active or pending)"
                )
            else:
                response.raise_for_status()

        except requests.exceptions.RequestException as e:
            print(f"Error deleting usecase: {e}")
            sys.exit(1)

    def update_usecase(
        self, usecase_id: str, name: str | None = None, description: str | None = None
    ) -> None:
        try:
            payload: dict[str, str | bool] = {}
            if name:
                payload["name"] = name
            if description:
                payload["description"] = description
            payload["isPublic"] = True

            if not payload:
                print("Error: Either name or description must be provided for update")
                sys.exit(1)

            response = requests.put(
                f"{self.pharia_api_os_usecases_base_url}/{usecase_id}",
                headers=self.headers,
                json=payload,
            )

            if response.status_code == 200:
                print(f"Successfully updated usecase {usecase_id}")
                if name:
                    print(f"  New name: {name}")
                if description:
                    print(f"  New description: {description}")
            else:
                print(f"Error: HTTP {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"Response: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"Response text: {response.text}")
                sys.exit(1)

        except requests.exceptions.RequestException as e:
            print(f"Error updating usecase: {e}")
            sys.exit(1)

    def deploy_usecase(self, usecase_id: str, config: dict | None = None) -> None:
        try:
            payload = config if config else {}
            response = requests.post(
                f"{self.pharia_api_os_usecases_base_url}/{usecase_id}/deployments",
                headers=self.headers,
                json=payload,
            )

            if response.status_code == 202:
                print(f"Deployment triggered for usecase {usecase_id}")
            else:
                print(f"Error: HTTP {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"Response: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"Response text: {response.text}")
                sys.exit(1)

        except requests.exceptions.RequestException as e:
            print(f"Error deploying usecase: {e}")
            sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Deploy supplier-briefing-no-chat service"
    )
    parser.add_argument(
        "command", choices=["list", "create", "delete", "deploy", "update"]
    )
    parser.add_argument("--description", help="Usecase description (for create/update)")
    parser.add_argument("--name", help="New usecase name (for update)")
    parser.add_argument(
        "--config", help="Deployment configuration JSON file (for deploy)"
    )
    parser.add_argument(
        "name_or_id",
        nargs="?",
        help="Usecase name (for create) or ID (for delete/deploy/update)",
    )

    args = parser.parse_args()

    deploy_settings = DeploySettings()  # type: ignore[call-arg]
    deployer = Deployer(deploy_settings)

    if args.command == "list":
        deployer.list_usecases()
    elif args.command == "create":
        if not args.name_or_id or not args.description:
            print("Error: name and --description are required for create command")
            sys.exit(1)
        deployer.create_usecase(args.name_or_id, args.description)
    elif args.command == "delete":
        if not args.name_or_id:
            print("Error: usecase ID is required for delete command")
            sys.exit(1)
        deployer.delete_usecase(args.name_or_id)
    elif args.command == "deploy":
        if not args.name_or_id:
            print("Error: usecase ID is required for deploy command")
            sys.exit(1)

        config = None
        if args.config:
            try:
                with open(args.config, "r") as f:
                    config = json.load(f)
                    # Replace environment variables in the config
                    config = Deployer.replace_env_vars(config, deploy_settings)
                    config = {"config": config}
            except Exception as e:
                print(f"Error loading config file: {e}")
                sys.exit(1)

        deployer.deploy_usecase(args.name_or_id, config)
    elif args.command == "update":
        if not args.name_or_id:
            print("Error: usecase ID is required for update command")
            sys.exit(1)
        if not args.name and not args.description:
            print(
                "Error: Either --name or --description is required for update command"
            )
            sys.exit(1)
        deployer.update_usecase(args.name_or_id, args.name, args.description)


if __name__ == "__main__":
    main()
