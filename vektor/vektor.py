import numpy as np
import transformers
import pickle
import tqdm

import vektor.lsh
import vektor.distance

import torch # yes, this is just for type-checking

transformers.logging.set_verbosity_error() # i just don't like the message
tokenizer = transformers.AutoTokenizer.from_pretrained("bert-base-uncased")
model = transformers.BertModel.from_pretrained("bert-base-uncased")

def bert_embedding(sentence: str) -> torch.Tensor:
    inputs = tokenizer(
        sentence,
        return_tensors = "pt",
        padding = "max_length",
        max_length = 100,
        truncation = True
    )
    outputs = model(**inputs)
    return outputs.last_hidden_state.detach()

class Vektor:
    def __init__(
        self,
        vectors: np.array = np.empty((1, 100, 768), dtype = np.float32),
        embedding: object = bert_embedding,
        distance: object = vektor.distance.cosine
    ) -> None:
        self.embedding = embedding
        self.distance = distance
        self.lsh = vektor.lsh.LSH(1 * 100 * 768)

    def from_source(self, source: list, key_fn: object = lambda x: x) -> None:
        for ref in (bar := tqdm.tqdm(source)):
            vector = np.array(self.embedding(key_fn(ref))).astype(np.float32)
            self.lsh.index(vector, ref)
            bar.set_description("from_source")

    def save(self, filename: str) -> None:
        with open(filename, "wb") as handler:
            pickle.dump(self.lsh, handler)

    def load(self, filename: str) -> None:
        with open(filename, "rb") as handler:
            self.lsh = pickle.load(handler)

    def query(self, sentence: str, top_k: int = 5) -> list:
        vector = np.array(self.embedding(sentence)).astype(np.float32)
        return self.lsh.query(vector, top_k, self.distance)