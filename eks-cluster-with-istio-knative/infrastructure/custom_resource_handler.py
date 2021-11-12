import json
import logging
import os
import subprocess

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# these are coming from the kubectl layer
os.environ["PATH"] = "/opt/kubectl:/opt/awscli:" + os.environ["PATH"]

outdir = os.environ.get("TEST_OUTDIR", "/tmp")
kubeconfig = os.path.join(outdir, "kubeconfig")


def on_event(event, context):
    print(event)
    print(context)

    request_type = event["RequestType"]
    if request_type == "Create":
        return on_create(event)
    if request_type == "Update":
        return on_update(event)
    if request_type == "Delete":
        return on_delete(event)
    raise Exception("Invalid request type: %s" % request_type)


def on_create(event):
    props = event["ResourceProperties"]
    print("create new resource with props %s" % props)

    update_kubeconfig(props)

    manifest = props["manifest"]
    label = props.get("label", None)

    kubectl("apply", manifest, label)

    return {"PhysicalResourceId": manifest}


def on_update(event):
    physical_id = event["PhysicalResourceId"]
    props = event["ResourceProperties"]
    old_props = event["OldResourceProperties"]
    print(f"update resource {physical_id} with {props}, {old_props}")
    update_kubeconfig(props)

    manifest = props["manifest"]
    label = props.get("label", None)

    kubectl("apply", manifest, label)


def on_delete(event):
    physical_id = event["PhysicalResourceId"]
    props = event["ResourceProperties"]
    print("delete resource %s" % physical_id)
    update_kubeconfig(props)

    manifest = props["manifest"]
    label = props.get("label", None)
    kubectl("delete", manifest, label)


def update_kubeconfig(props):
    # resource properties (all required)
    cluster_name = props["cluster_name"]
    role_arn = props["role_arn"]
    # "log in" to the cluster
    cmd = [
        "aws",
        "eks",
        "update-kubeconfig",
        "--role-arn",
        role_arn,
        "--name",
        cluster_name,
        "--kubeconfig",
        kubeconfig,
    ]
    logger.info(f"Running command: {cmd}")
    subprocess.check_call(cmd)

    if os.path.isfile(kubeconfig):
        os.chmod(kubeconfig, 0o600)


def kubectl(verb, file, label=None, *opts):
    maxAttempts = 3
    retry = maxAttempts
    if file.startswith("s3://"):
        file = download_s3_asset(file)
    while retry > 0:
        try:
            if label:
                cmd = ["kubectl", verb, "--kubeconfig", kubeconfig, "-l", label, "-f", file] + list(opts)
            else:
                cmd = ["kubectl", verb, "--kubeconfig", kubeconfig, "-f", file] + list(opts)
            logger.info(f"Running command: {cmd}")
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as exc:
            output = exc.output
            if b"i/o timeout" in output and retry > 0:
                retry = retry - 1
                logger.info("kubectl timed out, retries left: %s" % retry)
            elif b"no matches" in output:
                logger.info(output)
            elif b"the server could not find the requested" in output:
                logger.info(output)
            elif b"not found" in output:
                logger.info(output)
            else:
                logger.info(output)
                raise Exception(output)
        else:
            logger.info(output)
            return
    raise Exception(f"Operation failed after {maxAttempts} attempts: {output}")


def download_s3_asset(s3_object_url):
    import boto3

    bucket = s3_object_url.replace("s3://", "").split("/")[0]
    key = s3_object_url.replace(f"s3://{bucket}/", "")
    s3 = boto3.client("s3")
    s3.download_file(bucket, key, "/tmp/manifest.yaml")
    return "/tmp/manifest.yaml"
