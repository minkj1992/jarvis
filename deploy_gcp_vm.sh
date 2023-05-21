#!/bin/bash
# 이 스크립트는 GCP에서 가상 머신을 생성합니다.
# e2-standard-4 = vCPU 4개, 16GB RAM

# ./deploy_gcp_vm.sh tidy-amplifier-387210 asia-northeast3-a e2-standard-4 jarvis-instance

# 명령줄 인수를 확인합니다.
if [ $# -ne 4 ]; then
 echo "Usage: $0 PROJECT_ID ZONE MACHINE_TYPE MACHINE_NAME"
 exit 1
fi

# 변수를 초기화합니다.
PROJECT_ID=$1
ZONE=$2
MACHINE_TYPE=$3
MACHINE_NAME=$4
DNS_SYMBOL="jarvis-api-dns"
DNS_DESCRIPTION=""Jarvis GPT api server""
DNS_NAME="gptalk.store"

# gcloud 로그인을 합니다.
gcloud auth login
gcloud config set project $PROJECT_ID

# # 가상 머신을 생성합니다.
gcloud compute instances create $MACHINE_NAME \
 --project $PROJECT_ID \
 --zone $ZONE \
 --machine-type $MACHINE_TYPE \
 --image-family ubuntu-2004-lts \
 --image-project ubuntu-os-cloud \
 --boot-disk-size 10GB \
 --network default \
 --tags http-server,https-server

gcloud compute instances list

gcloud dns --project=$MACHINE_NAME managed-zones create $DNS_SYMBOL --description=$DNS_DESCRIPTION --dns-name=$DNS_NAME --visibility="public" --dnssec-state="on"

gcloud compute ssh $MACHINE_NAME

