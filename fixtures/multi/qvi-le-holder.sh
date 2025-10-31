#!/bin/bash
# To run this script you need to run the following command in separate terminals:
#   > kli witness demo
# and from the vLEI repo run:
#   > vLEI-server -s ./schema/acdc -c ./samples/acdc/ -o ./samples/oobis/
#

# issuer 1
# EEVlFHcMWAQNwezHjyKK5cKKzF6zgLlnrLyi_CcAEXCs
# issuer 2
# EFJtDtSoE6XOOqLoLvYoB7ctCzMtJDiAJltnXiK_EdlM
# issuee 1
# EI0IoYyHxXc7_uQyaN2WocSC3lRZsvrDAPbREOw7fM0_
# issuee 2
# EPw5WQAFcNXXSbg_pTKgh8-K_rfXnD1uDKS13OeNHkKE
# issuer group
# ELrnb8aI_wy2q_sSbCAwkgy2kOdMpRI1urFrhQiMJGLW
# issuee group
# ELkmm28zQEyxkryJZQ4WVT4fjukklM4dR91l2DQfQHZK

echo ${KERI_SCRIPT_DIR}

# Create local environments for issuer group
kli init --name issuer1 --salt 0ACDEyMzQ1Njc4OWxtbm9aBc --passcode DoB26Fj4x9LboAFWJra17O --config-dir ${KERI_SCRIPT_DIR} --config-file demo-witness-oobis
kli incept --passcode DoB26Fj4x9LboAFWJra17O --name issuer1 --alias issuer1 --file ${KERI_DEMO_SCRIPT_DIR}/data/issuer-1-sample.json

# Incept both local identifiers for issuer group
kli init --name issuer2 --salt 0ACDEyMzQ1Njc4OWdoaWpsaw --passcode DoB26Fj4x9LboAFWJra17O --config-dir ${KERI_SCRIPT_DIR} --config-file demo-witness-oobis
kli incept --passcode DoB26Fj4x9LboAFWJra17O --name issuer2 --alias issuer2 --file ${KERI_DEMO_SCRIPT_DIR}/data/issuer-2-sample.json

# Exchange OOBIs between issuer group
kli oobi resolve --passcode DoB26Fj4x9LboAFWJra17O --name issuer1 --oobi-alias issuer2 --oobi http://127.0.0.1:5642/oobi/EFJtDtSoE6XOOqLoLvYoB7ctCzMtJDiAJltnXiK_EdlM/witness
kli oobi resolve --passcode DoB26Fj4x9LboAFWJra17O --name issuer2 --oobi-alias issuer1 --oobi http://127.0.0.1:5642/oobi/EEVlFHcMWAQNwezHjyKK5cKKzF6zgLlnrLyi_CcAEXCs/witness

# Create the identifier to which the credential will be issued
kli init --name issuee1 --salt 0ACDEyMzQ1Njc4OWxtbm9qWc --passcode DoB26Fj4x9LboAFWJra17O --config-dir ${KERI_SCRIPT_DIR} --config-file demo-witness-oobis
kli incept --passcode DoB26Fj4x9LboAFWJra17O --name issuee1 --alias issuee1 --file ${KERI_DEMO_SCRIPT_DIR}/data/issuee-1-sample.json

# Create the identifier to which the credential will be issued
kli init --name issuee2 --salt 0ACDEyMzQ1Njc4OWxtbm9qWc --passcode DoB26Fj4x9LboAFWJra17O --config-dir ${KERI_SCRIPT_DIR} --config-file demo-witness-oobis
kli incept --passcode DoB26Fj4x9LboAFWJra17O --name issuee2 --alias issuee2 --file ${KERI_DEMO_SCRIPT_DIR}/data/issuee-2-sample.json

# Exchange OOBIs between issuee group
kli oobi resolve --passcode DoB26Fj4x9LboAFWJra17O --name issuee1 --oobi-alias issuee2 --oobi http://127.0.0.1:5642/oobi/EPw5WQAFcNXXSbg_pTKgh8-K_rfXnD1uDKS13OeNHkKE/witness
kli oobi resolve --passcode DoB26Fj4x9LboAFWJra17O --name issuee2 --oobi-alias issuee1 --oobi http://127.0.0.1:5642/oobi/EI0IoYyHxXc7_uQyaN2WocSC3lRZsvrDAPbREOw7fM0_/witness

# Introduce issuer to issuee
kli oobi resolve --passcode DoB26Fj4x9LboAFWJra17O --name issuee1 --oobi-alias issuer1 --oobi http://127.0.0.1:5642/oobi/EEVlFHcMWAQNwezHjyKK5cKKzF6zgLlnrLyi_CcAEXCs/witness
kli oobi resolve --passcode DoB26Fj4x9LboAFWJra17O --name issuee2 --oobi-alias issuer1 --oobi http://127.0.0.1:5642/oobi/EEVlFHcMWAQNwezHjyKK5cKKzF6zgLlnrLyi_CcAEXCs/witness
kli oobi resolve --passcode DoB26Fj4x9LboAFWJra17O --name issuee1 --oobi-alias issuer2 --oobi http://127.0.0.1:5642/oobi/EFJtDtSoE6XOOqLoLvYoB7ctCzMtJDiAJltnXiK_EdlM/witness
kli oobi resolve --passcode DoB26Fj4x9LboAFWJra17O --name issuee2 --oobi-alias issuer2 --oobi http://127.0.0.1:5642/oobi/EFJtDtSoE6XOOqLoLvYoB7ctCzMtJDiAJltnXiK_EdlM/witness

# Introduce the issuee to issuer
kli oobi resolve --passcode DoB26Fj4x9LboAFWJra17O --name issuer1 --oobi-alias issuee1 --oobi http://127.0.0.1:5642/oobi/EI0IoYyHxXc7_uQyaN2WocSC3lRZsvrDAPbREOw7fM0_/witness
kli oobi resolve --passcode DoB26Fj4x9LboAFWJra17O --name issuer2 --oobi-alias issuee1 --oobi http://127.0.0.1:5642/oobi/EI0IoYyHxXc7_uQyaN2WocSC3lRZsvrDAPbREOw7fM0_/witness
kli oobi resolve --passcode DoB26Fj4x9LboAFWJra17O --name issuer1 --oobi-alias issuee2 --oobi http://127.0.0.1:5642/oobi/EPw5WQAFcNXXSbg_pTKgh8-K_rfXnD1uDKS13OeNHkKE/witness
kli oobi resolve --passcode DoB26Fj4x9LboAFWJra17O --name issuer2 --oobi-alias issuee2 --oobi http://127.0.0.1:5642/oobi/EPw5WQAFcNXXSbg_pTKgh8-K_rfXnD1uDKS13OeNHkKE/witness

## Load Data OOBI for schema of credential to issue
kli oobi resolve --passcode DoB26Fj4x9LboAFWJra17O --name issuer1 --oobi-alias vc --oobi http://127.0.0.1:7723/oobi/EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao
kli oobi resolve --passcode DoB26Fj4x9LboAFWJra17O --name issuer2 --oobi-alias vc --oobi http://127.0.0.1:7723/oobi/EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao
kli oobi resolve --passcode DoB26Fj4x9LboAFWJra17O --name issuee1 --oobi-alias vc --oobi http://127.0.0.1:7723/oobi/EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao
kli oobi resolve --passcode DoB26Fj4x9LboAFWJra17O --name issuee2 --oobi-alias vc --oobi http://127.0.0.1:7723/oobi/EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao

# Run the follow in parallel and wait for the issuer group to be created:
kli multisig incept --passcode DoB26Fj4x9LboAFWJra17O --name issuer1 --alias issuer1 --group issuer --file ${KERI_DEMO_SCRIPT_DIR}/data/issuer-multisig-sample.json &
pid=$!
PID_LIST="$pid"

kli multisig incept --passcode DoB26Fj4x9LboAFWJra17O --name issuer2 --alias issuer2 --group issuer --file ${KERI_DEMO_SCRIPT_DIR}/data/issuer-multisig-sample.json &
pid=$!
PID_LIST+=" $pid"

wait $PID_LIST

# Run the follow in parallel and wait for the issuee group to be created:
kli multisig incept --passcode DoB26Fj4x9LboAFWJra17O --name issuee1 --alias issuee1 --group issuee --file ${KERI_DEMO_SCRIPT_DIR}/data/issuee-multisig-sample.json &
pid=$!
PID_LIST="$pid"

kli multisig incept --passcode DoB26Fj4x9LboAFWJra17O --name issuee2 --alias issuee2 --group issuee --file ${KERI_DEMO_SCRIPT_DIR}/data/issuee-multisig-sample.json &
pid=$!
PID_LIST+=" $pid"

wait $PID_LIST

# Introduce issuer issuer issuer to issuees
kli oobi resolve --passcode DoB26Fj4x9LboAFWJra17O --name issuer1 --oobi-alias issuee --oobi http://127.0.0.1:5642/oobi/ELkmm28zQEyxkryJZQ4WVT4fjukklM4dR91l2DQfQHZK/witness
kli oobi resolve --passcode DoB26Fj4x9LboAFWJra17O --name issuer2 --oobi-alias issuee --oobi http://127.0.0.1:5642/oobi/ELkmm28zQEyxkryJZQ4WVT4fjukklM4dR91l2DQfQHZK/witness

kli oobi resolve --passcode DoB26Fj4x9LboAFWJra17O --name issuee1 --oobi-alias issuer --oobi http://127.0.0.1:5642/oobi/ELrnb8aI_wy2q_sSbCAwkgy2kOdMpRI1urFrhQiMJGLW/witness
kli oobi resolve --passcode DoB26Fj4x9LboAFWJra17O --name issuee2 --oobi-alias issuer --oobi http://127.0.0.1:5642/oobi/ELrnb8aI_wy2q_sSbCAwkgy2kOdMpRI1urFrhQiMJGLW/witness
