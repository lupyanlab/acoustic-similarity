library(magrittr)
library(dplyr)
library(readr)

# devtools::install_github('lupyanlab/words-in-transition',
#                          subdir = 'wordsintransition')
library(wordsintransition)
data("transcription_matches")

transcription_matches %<>%
  recode_question_type %>%
  recode_message_type %>%
  recode_version %>%
  label_outliers %>%
  filter(is_outlier == 0, question_type != "catch_trial")

words <- unique(transcription_matches$word)
write.table(words, "data/words/words.txt", row.names = FALSE, col.names = FALSE)
