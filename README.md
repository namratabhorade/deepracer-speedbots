# deepracer-speedbots

DeepRacer Commands

vim //home/cloudshell-user/deepracer-on-the-spot/custom-files/run.env


DR_WORLD_NAME=arctic_open_ccw
DR_LOCAL_S3_MODEL_PREFIX=MUDR24-296-MODEL-201
DR_LOCAL_S3_CUSTOM_FILES_PREFIX=custom_files/$DR_WORLD_NAME/$DR_LOCAL_S3_MODEL_PREFIX



cd //home/cloudshell-user/
rm //home/cloudshell-user/reward_function.py
rm //home/cloudshell-user/model_metadata.json
rm //home/cloudshell-user/hyperparameters.json
ls -ltr

----------------------------------------------------

cp //home/cloudshell-user/reward_function.py //home/cloudshell-user/deepracer-on-the-spot/custom-files/reward_function.py
cp //home/cloudshell-user/model_metadata.json //home/cloudshell-user/deepracer-on-the-spot/custom-files/model_metadata.json
cp //home/cloudshell-user/hyperparameters.json //home/cloudshell-user/deepracer-on-the-spot/custom-files/hyperparameters.json

----------------------------------------------------

cd //home/cloudshell-user/deepracer-on-the-spot/
./create-spot-instance.sh MUDR24-296-base MUDR24-296-MODEL-201 120

————————————————————————————

./add-access.sh MUDR24-296-base namrata-access 58.146.118.20

----------------------------------------------------

cd //home/cloudshell-user/deep racer-on-the-spot/
./stop-training.sh MUDR24-296-MODEL-123

----------------------------------------------------