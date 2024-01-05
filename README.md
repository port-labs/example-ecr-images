# example-ecr-images
Python Script for Ingesting ECR Images in Port

## Getting started
In this example, you will create blueprints for `ecrImage` and `ecrRepository` that ingests images and repositories from ECR into Port. You will then use a Python script to make API calls to AWS ECR REST API to fetch the data from your account.

### Blueprints
Create the following blueprints in Port using the schemas:


#### Repository
```json
{
  "identifier": "ecrRepository",
  "description": "This blueprint represents an ECR Repository",
  "title": "ECR Repository",
  "icon": "AWS",
  "schema": {
    "properties": {
        "name": {
            "type": "string",
            "title": "Repository Name",
            "description": "The name of the repository",
        },
        "registryId": {
            "type": "string",
            "title": "Registry ID",
            "description": "The ID of the registry",
        },
      "arn": {
        "type": "string",
        "title": "Repository ARN",
        "description": "The ARN of the repository",
      },
      "uri": {
        "type": "string",
        "title": "Repository URI",
        "description": "The URI of the repository",
      },
        "createdAt": {
            "type": "string",
            "title": "Created At",
            "description": "Date and time the repository was created",
            "format": "date-time"
        },
      "imageTagMutability": {
        "type": "string",
        "title": "Image Tag Mutability",
        "description": "The image tag mutability setting for the repository",
        "enum": [
          "MUTABLE",
          "IMMUTABLE"
        ],
        "enumColors": {
            "MUTABLE": "green",
            "IMMUTABLE": "darkGray"
        }
      },
      "configurationScanOnPush": {
        "type": "boolean",
        "title": "Configuration Scan on Push",
        "description": "Image scanning configuration when pushing images to this repository",
      },
      "encryptionType": {
        "type": "string",
        "title": "Encryption Type",
        "description": "The encryption type of the repository",
        "enum": [
          "AES256",
          "KMS"
        ],
        "enumColors": {
            "AES256": "green",
            "KMS": "blue"
        }
      },
      "kmsKey": {
        "type": "string",
        "title": "KMS Key",
        "description": "The KMS key used for encryption",
      }
    },
    "required": []
  },
  "mirrorProperties": {},
  "calculationProperties": {},
  "aggregationProperties": {},
  "relations": {}
}
```

#### Image
```json
{
  "identifier": "ecrImage",
  "description": "This blueprint represents an ECR image",
  "title": "ECR Image",
  "icon": "AWS",
  "schema": {
    "properties": {
      "registryId": {
        "type": "string",
        "title": "Registry ID",
        "description": "The ID of the registry"
      },
      "digest": {
        "type": "string",
        "title": "Image Digest",
        "description": "SHA256 digest of image manifest"
      },
      "tags": {
        "type": "array",
        "title": "Image Tags",
        "description": "List of tags for the image"
      },
      "size": {
        "type": "number",
        "title": "Image Size",
        "description": "Size of the image in bytes"
      },
      "pushedAt": {
        "type": "string",
        "title": "Pushed At",
        "description": "Date and time the image was pushed to the repository",
        "format": "date-time"
      },
      "manifestMediaType": {
        "type": "string",
        "title": "Manifest Media Type",
        "description": "The media type of the image manifest"
      },
      "artifactMediaType": {
        "type": "string",
        "title": "Artifact Media Type",
        "description": "The media type of the image artifact"
      },
      "lastRecordedPullTime": {
        "type": "string",
        "title": "Last Recorded Pull Time",
        "description": "Date and time the image was last pulled",
        "format": "date-time"
      }
    },
    "required": []
  },
  "mirrorProperties": {},
  "calculationProperties": {},
  "aggregationProperties": {},
  "relations": {
    "repository": {
      "title": "ECR Repository",
      "description": "Repository of the image",
      "target": "ecrRepository",
      "required": true,
      "many": false
    }
  }
}
```

### Running the Python script
First clone the repository and cd into the work directory with:
```bash
$ git clone git@github.com:port-labs/example-ecr-images.git
$ cd example-ecr-images
```

Install the needed dependencies within the context of a virtual environment with:
```bash
$ virtualenv venv
$ source venv/bin/activate
$ pip3 install -r requirements.txt
```

To ingest your data, you need to populate some environment variables. You can do that by either duplicating the `.example.env` file and renaming the copy as `.env`, then edit the values as needed; or run the commands below in your terminal:

```bash
export PORT_CLIENT_ID=port_client_id
export PORT_CLIENT_SECRET=port_client_secret
export AWS_ACCESS_KEY_ID=aws_access_key_id
export AWS_SECRET_ACCESS_KEY=aws_secret_access_key
export AWS_DEFAULT_REGION=aws_default_region
export AWS_REGISTRY_ID=aws_account_id
```

Then run the script with:
```bash
$ python app.py
```

Each variable required are:
- PORT_CLIENT_ID: Port Client ID
- PORT_CLIENT_SECRET: Port Client secret
- AWS_ACCESS_KEY_ID: AWS access key ID
- AWS_SECRET_ACCESS_KEY: AWS secret access key
- AWS_DEFAULT_REGION: AWS default region where the ECR repository is located
- AWS_REGISTRY_ID: AWS account ID