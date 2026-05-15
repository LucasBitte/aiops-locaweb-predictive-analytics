import paramiko
import os
import sys
from dotenv import load_dotenv

_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(_root_dir, ".env"))


def get_config():
    host = os.getenv("VPS_HOST")
    user = os.getenv("VPS_USER")
    password = os.getenv("VPS_PASSWORD")
    key_path = os.getenv("VPS_KEY_PATH")
    dags_path = os.getenv("VPS_DAGS_PATH")
    container = os.getenv("VPS_AIRFLOW_CONTAINER")
    local_dags_dir = os.getenv("LOCAL_DAGS_PATH", ".")

    missing = [k for k, v in {"VPS_HOST": host, "VPS_USER": user}.items() if not v]
    if missing:
        print(f"❌ Variáveis ausentes no .env: {', '.join(missing)}")
        sys.exit(1)

    if not password and not key_path:
        print("❌ Defina VPS_PASSWORD ou VPS_KEY_PATH no .env")
        sys.exit(1)

    if not dags_path and not container:
        print("❌ Defina VPS_DAGS_PATH ou VPS_AIRFLOW_CONTAINER no .env")
        sys.exit(1)

    return host, user, password, key_path, dags_path, container, local_dags_dir


def connect_ssh(host, user, password, key_path):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    if key_path:
        ssh.connect(hostname=host, username=user, key_filename=os.path.expanduser(key_path))
    else:
        ssh.connect(hostname=host, username=user, password=password)
    return ssh


def deploy_via_sftp(sftp, local_path, dags_path, dag_filename):
    remote_path = os.path.join(dags_path, dag_filename)
    sftp.put(local_path, remote_path)


def deploy_via_docker_cp(ssh, sftp, local_path, container, dag_filename):
    tmp_remote = f"/tmp/{dag_filename}"
    sftp.put(local_path, tmp_remote)

    cmd = f"docker cp {tmp_remote} {container}:/opt/airflow/dags/{dag_filename}"
    _, stdout, stderr = ssh.exec_command(cmd)
    if stdout.channel.recv_exit_status() != 0:
        raise RuntimeError(stderr.read().decode().strip())

    ssh.exec_command(f"rm -f {tmp_remote}")


def main():
    host, user, password, key_path, dags_path, container, local_dags_dir = get_config()

    dags = [f for f in os.listdir(local_dags_dir) if f.endswith(".py")]
    if not dags:
        print(f"❌ Nenhum arquivo .py encontrado em: {local_dags_dir}")
        sys.exit(1)

    print(f"⏳ Conectando à VPS {host} como {user}...")
    try:
        ssh = connect_ssh(host, user, password, key_path)
        sftp = ssh.open_sftp()
        print(f"🔗 Conexão estabelecida. Enviando {len(dags)} DAG(s)...\n")

        sucesso, falha = [], []
        for dag_filename in sorted(dags):
            local_path = os.path.join(local_dags_dir, dag_filename)
            try:
                if container:
                    deploy_via_docker_cp(ssh, sftp, local_path, container, dag_filename)
                else:
                    deploy_via_sftp(sftp, local_path, dags_path, dag_filename)
                print(f"  ✅ {dag_filename}")
                sucesso.append(dag_filename)
            except Exception as e:
                print(f"  ❌ {dag_filename}: {e}")
                falha.append(dag_filename)

        sftp.close()
        ssh.close()

        print(f"\n📊 Resultado: {len(sucesso)} enviada(s), {len(falha)} com erro.")
        if falha:
            print(f"⚠️  Com erro: {', '.join(falha)}")
            sys.exit(1)
        print("💡 Aguarde 30–60 segundos para o Airflow detectar as DAGs.")

    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
