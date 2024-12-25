from os import getenv

import boto3
from flask import current_app, url_for
from .. import db
from ..auth import notify

gridfs_imgs = db.ImageGridFsProxy(collection_name='images')

s3_host = getenv('S3_HOST')
s3_bucket = getenv('S3_BUCKET')
s3_key = getenv('S3_KEY')
s3_secret = getenv('S3_SECRET')

s3_active = False
if s3_host and s3_bucket and s3_key and s3_secret:
    s3_active = True

if s3_active:
    session = boto3.session.Session()
    s3_client = session.client('s3', **{
        "region_name": s3_host.split('.')[0],
        "endpoint_url": "https://" + s3_host,
        "aws_access_key_id": s3_key,
        "aws_secret_access_key": s3_secret,
    })
# elif not current_app.debug:
#     print("Produção sem Credencial S3!")
#     exit(9)

def get_buckets():
    response = s3_client.list_buckets()
    print('Existing buckets:')
    for bucket in response['Buckets']:
        print(f'  {bucket["Name"]}')

def upload_file(buf, app, file, bucket=s3_bucket, acl='private'):
    if s3_active:
        fbytes = buf.getvalue()
        response = s3_client.put_object(
            Bucket=bucket,
            Key=str(file.id),
            Body=fbytes,
            ContentType=file.content_type,
            ACL=acl,
            Tagging=f"app={app}",
            Metadata={'app': app},
        )
    else:
        if file.img:
            response = file.img.replace(buf, app=app, content_type=file.content_type)
        else:
            response = file.img.put(buf, app=app, content_type=file.content_type)
        file.save()
    return response

def download_file(file, external=False, bucket=s3_bucket):
    if s3_active:
        response = s3_client.generate_presigned_url(
            ClientMethod='get_object',
            Params={'Bucket': bucket,
                    'Key': str(file.id)},
            ExpiresIn=300)
        return response
    elif external:
        # internal_url = url_for('fs.fs', digitizer=img.img.grid_id, _external=True)
        # internal_domain = internal_url.split('://')[1].split('/')[0]
        # external_url = internal_url.replace(internal_domain, current_app.config['DOMAIN'])
        # return external_url
        return url_for('fs.fs', digitizer=file.img.grid_id, _external=True)
    else:
        return url_for('fs.fs', digitizer=file.img.grid_id)

def delete_file(file, bucket=s3_bucket):
    if file.img and file.img.get('_id'):
        gridfs_imgs.fs.delete(file.img._id)
        file.img.delete()
    if s3_active:
        response = s3_client.delete_object(
            Bucket=bucket,
            Key=str(file.id),
        )

        if not (response.get('ResponseMetadata') and
            response['ResponseMetadata'].get('HTTPStatusCode') and
                response['ResponseMetadata']['HTTPStatusCode'] == 204
        ):
            notify('Erro deletando arquivo do s3', response)


# copied = s3_client.copy_object(Bucket=bucket, CopySource=f'{bucket}/{key}', Key=newkey)
