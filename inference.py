import librosa
import torch
import os
import argparse
#huggingface code
import torchaudio
import evaluate

from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC
from tqdm import tqdm

class Inferencer:
    def __init__(self, device, huggingface_folder, model_path) -> None:
        self.device = device
        self.processor = Wav2Vec2Processor.from_pretrained(huggingface_folder)
        self.model = Wav2Vec2ForCTC.from_pretrained(huggingface_folder).to(self.device)
        # if model_path exist (not from huggingface)
        if model_path is not None:
            self.preload_model(model_path)


    def preload_model(self, model_path) -> None:
        """
        Preload model parameters (in "*.tar" format) at the start of experiment.
        Args:
            model_path: The file path of the *.tar file
        """
        assert os.path.exists(model_path), f"The file {model_path} is not exist. please check path."
        checkpoint = torch.load(model_path, map_location=self.device)
        self.model.load_state_dict(checkpoint["model"], strict = True)
        print(f"Model preloaded successfully from {model_path}.")


    def transcribe(self, wav) -> str:
        # input_values = self.processor(wav, sampling_rate=16000, return_tensors="pt").input_values
        # data/clips/Ind001_F_B_C_news_0000.wav
        # tensor([[ 0.0066, -0.0033, -0.0022,  ..., -0.0011, -0.0011, -0.0055]]) --> attention_mask ga diambil

        inputs = self.processor(wav, sampling_rate=16000, return_tensors="pt", padding=True)
        # data/clips/Ind001_F_B_C_news_0000.wav
        # {'input_values': tensor([[ 0.0066, -0.0033, -0.0022,  ..., -0.0011, -0.0011, -0.0055]]), 'attention_mask': tensor([[1, 1, 1,  ..., 1, 1, 1]], dtype=torch.int32)}
        
        with torch.no_grad():
            #logits = self.model(input_values.to(self.device)).logits
            logits = self.model(inputs.input_values.to(self.device),attention_mask=inputs.attention_mask.to(self.device)).logits
        pred_ids = torch.argmax(logits, dim=-1)
        pred_transcript = self.processor.batch_decode(pred_ids)[0]
        return pred_transcript

    def run(self, test_filepath):
        filename = test_filepath.split('/')[-1].split('.')[0] #[-1] indicate the last substring of the list
        filetype = test_filepath.split('.')[1]
        print("FILETYPE:",filetype)

        #filetype could be list of path (txt) or wav
        if filetype == 'txt':
            f = open(test_filepath, 'r')
            lines = f.read().splitlines()
            f.close()

            f = open(test_filepath.replace(filename, 'transcript_'+filename), 'w+')
            for line in tqdm(lines):
                audio_path = line.split('\t')[0].strip()
                path = "/".join(["data/clips",audio_path])
                print(path)
                # wav, _ = librosa.load(path, sr = 16000)
                wav, _ = torchaudio.load(path)
                wav = wav.squeeze().numpy()

                transcript = self.transcribe(wav)
                f.write(audio_path + ' ' + transcript + '\n')
            f.close()


        else:
            # single audio file
            wav, _ = librosa.load(test_filepath, sr = 16000)

            # hugging face code
            speech_array, sampling_rate = torchaudio.load(test_filepath) #works
            #resampler = torchaudio.transforms.Resample(sampling_rate, 16_000)
            speech = speech_array.squeeze().numpy()

            #wer
            wer = evaluate.load('wer')
            print(f"wer: {wer.compute(references=[self.transcribe(speech)], predictions=['elsasharif mengaku'])}") #works


            print(f"transcript 1: {self.transcribe(wav)}") #works
            print(f"transcript 2: {self.transcribe(speech)}") #works


if __name__ == '__main__':
    args = argparse.ArgumentParser(description='ASR INFERENCE ARGS')
    args.add_argument('-f', '--test_filepath', type=str, required = True,
                      help='It can be either the path to your audio file (.wav, .mp3) or a text file (.txt) containing a list of audio file paths.')
    args.add_argument('-s', '--huggingface_folder', type=str, default = 'huggingface-hub',
                      help='The folder where you stored the huggingface files. Check the <local_dir> argument of [huggingface.args] in config.toml. Default value: "huggingface-hub".')
    args.add_argument('-m', '--model_path', type=str, default = None,
                      help='Path to the model (.tar file) in saved/<project_name>/checkpoints. If not provided, default uses the pytorch_model.bin in the <HUGGINGFACE_FOLDER>')
    args.add_argument('-d', '--device_id', type=int, default = 0,
                      help='The device you want to test your model on if CUDA is available. Otherwise, CPU is used. Default value: 0')
    args = args.parse_args()
    
    device = f"cuda:{args.device_id}" if torch.cuda.is_available() else "cpu"

    inferencer = Inferencer(
        device = device, 
        huggingface_folder = args.huggingface_folder, 
        model_path = args.model_path)

    inferencer.run(args.test_filepath)

