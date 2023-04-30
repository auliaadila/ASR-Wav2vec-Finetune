#!/bin/bash

# SINGLE AUDIO
# python inference.py \
#     -f data/Ind001_F_B_C_news_0000.wav \
#     -s indonesian-nlp/wav2vec2-large-xlsr-indonesian

# LIST OF AUDIO
python inference.py \
    -f data/metadata.txt \
    -s indonesian-nlp/wav2vec2-large-xlsr-indonesian