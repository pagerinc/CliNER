
import numpy as np
from word2vec import embeddings

def get_surrounding_embeddings(chunked_sentence, index):

    # TODO:  normalise?
    #        by dimension?
    #        by num of chunks?
    #        by tokens with embeddings?

    surrounding_chunks = chunked_sentence[index-2:index] + chunked_sentence[index+1:index+3]

    embedding_sum = np.zeros((300,))

    for chunk in surrounding_chunks:

        chunk = chunk.split(' ')

        for token in chunk:

            if token in embeddings:

                embedding_sum += embeddings[token]

    return {"embedding_{}".format(i):entry for i, entry in enumerate(embedding_sum)}


def get_lexical_vectors(token, gram_mappings):

    grams_in_token = []

    # TODO: make thos a parameter
    lexical_vect = np.zeros(200)

    for gram in gram_mappings:

        if gram in token:

            grams_in_token.append(gram)

            lexical_vect += gram_mappings[gram]

    return (lexical_vect/np.linalg.norm(lexical_vect))


def get_sequence_vectors(chunk, skipgram_mappings, word_embeddings):

    tokens = chunk.split(' ')

    summed_embeddings = None
    summed_lexical_vectors = None

    for token in tokens:

        if token in word_embeddings:

            if summed_lexical_vectors is None:
                summed_lexical_vectors = get_lexical_vectors(token, skipgram_mappings)
            else:
                summed_lexical_vectors += get_lexical_vectors(token, skipgram_mappings)

        else:

            continue

        if summed_embeddings is None:
            summed_embeddings = word_embeddings[token]
        else:
            summed_embeddings += word_embeddings[token]

    if summed_embeddings is None:

        assert summed_lexical_vectors is None

        for token in tokens:

            if summed_lexical_vectors is None:
                summed_lexical_vectors = get_lexical_vectors(token, skipgram_mappings)
            else:
                summed_lexical_vectors += get_lexical_vectors(token, skipgram_mappings)

    normed_lexical_vectors = (summed_lexical_vectors / np.linalg.norm(summed_lexical_vectors))

    if summed_embeddings is None:
        return normed_lexical_vectors
    else:
        sequence_embeddings = np.append(summed_embeddings / np.linalg.norm(summed_embeddings), normed_lexical_vectors)
        normed_sequence_embeddings = (sequence_embeddings / np.linalg.norm(sequence_embeddings))
        return normed_sequence_embeddings

if __name__ == "__main__":

    print len(embeddings)




