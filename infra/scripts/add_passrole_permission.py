"""
Add iam:PassRole permission to aiops-deployer user
Para permitir criar Glue jobs usando uma role IAM existente
"""

import boto3
import json
from dotenv import load_dotenv

load_dotenv()

iam_client = boto3.client('iam')
user_name = 'aiops-deployer'

# Policy que permite PassRole para a role de Glue
passrole_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "iam:PassRole",
            "Resource": "arn:aws:iam::206226812451:role/aiops-glue-bronze-silver-role"
        }
    ]
}

try:
    print(f"Adicionando iam:PassRole ao usuário {user_name}...")
    iam_client.put_user_policy(
        UserName=user_name,
        PolicyName="aiops-glue-passrole-policy",
        PolicyDocument=json.dumps(passrole_policy)
    )
    print(f"✅ Permissão iam:PassRole adicionada com sucesso!")
    print(f"\nAgora você pode rodar novamente:")
    print(f"  python infra/scripts/deploy_glue_job.py")
except Exception as e:
    print(f"❌ Erro ao adicionar permissão: {e}")
    print(f"\nAlternativa: Adicione manualmente via AWS Console")
    print(f"1. Vá para IAM → Users → aiops-deployer")
    print(f"2. Add inline policy com este JSON:")
    print(json.dumps(passrole_policy, indent=2))
