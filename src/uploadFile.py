import boto3, os
from botocore.exceptions import NoCredentialsError
from dotenv import load_dotenv
load_dotenv()


session = boto3.Session(profile_name=os.getenv("AWS_LOCAL_PROFILE_NAME"))

def upload_to_s3(file_name, bucket_name):
    print(f"\nSubiendo ARCHIVO {file_name} al BUCKET {bucket_name}")
    object_name = file_name

    s3_client = session.client('s3')
    try:
        s3_client.upload_file(file_name, bucket_name, object_name)
        print(f"\nArchivo {file_name} subido correctamente a {bucket_name}/{object_name}")

        url = generate_presigned_url(s3_client, bucket_name, object_name)
        return url

    except NoCredentialsError:
        print("Error: No se encuentran las credenciales de AWS.")
    except Exception as e:
        print(f"Error al subir el archivo: {e}")

def generate_presigned_url(s3_client, bucket_name, object_name, expiration=3600):
    try:
        response = s3_client.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': object_name}, ExpiresIn=expiration)
        return response
    except Exception as e:
        print(f"Error al generar URL prefirmada: {e}")
        return None