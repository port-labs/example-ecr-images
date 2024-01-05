import asyncio
import logging
import os
from typing import Any

import aiohttp
import boto3
import dotenv
import requests

dotenv.load_dotenv()

logger = logging.getLogger(__name__)

PORT_API_URL = "https://api.getport.io/v1"
PORT_CLIENT_ID = os.getenv("PORT_CLIENT_ID")
PORT_CLIENT_SECRET = os.getenv("PORT_CLIENT_SECRET")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
AWS_REGISTRY_ID = os.getenv("AWS_REGISTRY_ID")

ECR_REPOSITORY_BLUEPRINT = "ecrRepository"
ECR_IMAGE_BLUEPRINT = "ecrImage"
MAX_RESULTS = 999


# Get Port Access Token
credentials = {"clientId": PORT_CLIENT_ID, "clientSecret": PORT_CLIENT_SECRET}
token_response = requests.post(f"{PORT_API_URL}/auth/access_token", json=credentials)
access_token = token_response.json()["accessToken"]

# You can now use the value in access_token when making further requests
headers = {"Authorization": f"Bearer {access_token}"}

client = boto3.client("ecr", region_name=AWS_DEFAULT_REGION)


async def add_entity_to_port(
    session: aiohttp.ClientSession, blueprint_id, entity_object
):
    """A function to create the passed entity in Port

    Params
    --------------
    blueprint_id: str
        The blueprint id to create the entity in Port

    entity_object: dict
        The entity to add in your Port catalog

    Returns
    --------------
    response: dict
        The response object after calling the webhook
    """
    logger.info(f"Adding entity to Port: {entity_object}")
    response = await session.post(
        (
            f"{PORT_API_URL}/blueprints/"
            f"{blueprint_id}/entities?upsert=true&merge=true"
        ),
        json=entity_object,
        headers=headers,
    )
    if not response.ok:
        logger.info("Ingesting {blueprint_id} entity to port failed, skipping...")
    logger.info(f"Added entity to Port: {entity_object}")


async def get_all_repositories(session: aiohttp.ClientSession):
    """A function to get all repositories from ECR

    Returns
    --------------
    repositories: list
        A list of all repositories in an ECR registry
    """
    next_token = None
    kwargs = {}
    logger.info("Getting all repositories from ECR")

    while True:
        if next_token:
            kwargs = {"nextToken": next_token}

        response = client.describe_repositories(
            registryId=AWS_REGISTRY_ID,
            maxResults=MAX_RESULTS,
            **kwargs,
        )
        yield response["repositories"]
        next_token = response.get("nextToken")
        if not next_token:
            break
    logger.info(f"Got all repositories from ECR registry: {AWS_REGISTRY_ID}")


async def get_all_images(session: aiohttp.ClientSession, repository_name):
    """A function to get all images from a repository in ECR

    Params
    --------------
    repository_name: str
        The name of the repository to get images from

    Returns
    --------------
    images: list
        A list of all images in a repository
    """
    next_token = None
    kwargs = {}
    logger.info(f"Getting all images from ECR repository: {repository_name}")

    while True:
        if next_token:
            kwargs = {"nextToken": next_token}

        response = client.describe_images(
            registryId=AWS_REGISTRY_ID,
            repositoryName=repository_name,
            maxResults=MAX_RESULTS,
            **kwargs,
        )
        yield response["imageDetails"]
        next_token = response.get("nextToken")
        if not next_token:
            break

    logger.info(f"Got all images from ECR repository: {repository_name}")


async def ingest_ecr_repositories(
    session: aiohttp.ClientSession, repository: dict[str, Any]
):
    encryption_type = None
    kms_key = None
    encryption_configuration = repository.get("encryptionConfiguration")

    if encryption_configuration:
        encryption_type = encryption_configuration.get("encryptionType")
        kms_key = encryption_configuration.get("kmsKey")

    repository_object = {
        "registryId": repository["registryId"],
        "arn": repository["repositoryArn"],
        "uri": repository["repositoryUri"],
        "createdAt": repository["createdAt"].strftime("%Y-%m-%dT%H:%M:%SZ"),
        "imageTagMutability": repository["imageTagMutability"],
        "configurationScanOnPush": repository["imageScanningConfiguration"][
            "scanOnPush"
        ],
        "encryptionType": encryption_type,
        "kmsKey": kms_key,
    }
    entity_object = {
        "identifier": repository["repositoryName"],
        "title": repository_object["name"],
        "properties": {**repository_object},
    }

    await add_entity_to_port(session, ECR_REPOSITORY_BLUEPRINT, entity_object)


async def ingest_ecr_images(session: aiohttp.ClientSession, image: dict[str, Any]):
    last_recorded_pull_time = image.get("lastRecordedPullTime")
    if last_recorded_pull_time:
        last_recorded_pull_time = last_recorded_pull_time.strftime("%Y-%m-%dT%H:%M:%SZ")

    entity_object = {
        "identifier": image["imageDigest"],
        "title": image["imageDigest"],
        "properties": {
            "registryId": image["registryId"],
            "digest": image["imageDigest"],
            "tags": image["imageTags"],
            "size": image["imageSizeInBytes"],
            "pushedAt": image["imagePushedAt"].strftime("%Y-%m-%dT%H:%M:%SZ"),
            "manifestMediaType": image["imageManifestMediaType"],
            "artifactMediaType": image["artifactMediaType"],
            "lastRecordedPullTime": last_recorded_pull_time,
        },
        "relations": {
            "repository": image["repositoryName"],
        },
    }
    await add_entity_to_port(session, ECR_IMAGE_BLUEPRINT, entity_object)


async def main():
    logger.info("Starting Port integration")
    async with aiohttp.ClientSession() as session:
        async for repositories in get_all_repositories(session):
            for repository in repositories:
                await ingest_ecr_repositories(session, repository)

                async for images in get_all_images(
                    session, repository["repositoryName"]
                ):
                    for image in images:
                        await ingest_ecr_images(session, image)

    logger.info("Finished Port integration")


if __name__ == "__main__":
    asyncio.run(main())
