import itertools
import numpy as np

from PIL import Image
from jina import requests, DocumentArray, Executor
from typing import Any, Iterator, List, Optional, Sequence

from .model import ClothingSegmentationModel, PillowImage


class ClothingSegmenter(Executor):
    """
    An executor that can be used to perform segmentation on images of fashion products
    It is based on a U2NET architecture pre-trained on iMaterialistic fashion 2019
    The executor detects the parts of the images that represent clothing or fashion items and
    filters out the rest of the image content.
    """

    SHAPE = (768, 500)

    def __init__(self, model_path: str, batch_size: int = 32, **kwargs) -> None:
        """
        Initialization

        :param model_path: The path to the pre-trained U2NET model
        :param batch_size: The inference batch size
        """
        super().__init__(**kwargs)
        self._model = ClothingSegmentationModel(model_path=model_path)
        self._batch_size = batch_size


    def _reshape_docs(self, docs: DocumentArray) -> None:
        """Reshape Jina docs to the correct shape"""
        for doc in docs:
            doc.set_image_tensor_shape(self.SHAPE)
        return docs

    # @staticmethod
    # def _docs_to_images(docs: DocumentArray):
    #     """Convert Jina docs to Pillow images"""
    #     return [Image.fromarray(doc.blob) for doc in docs]

    # @staticmethod
    # def _generate_batches(sequence: Sequence[Any], size: int) -> Iterator[Any]:
    #     """Generate batches of length 'size' from a sequence"""
    #     iterable: Iterator[Any] = iter(sequence)
    #     return iter(lambda: list(itertools.islice(iterable, size)), [])

    @staticmethod
    def _update_blobs(docs: DocumentArray, images: List[PillowImage]) -> None:
        """Update document blobs with the segmented images"""
        for doc, image in zip(docs, images):
            doc.content = np.array(image)

    @requests
    def segment(self, docs: DocumentArray, **_) -> Optional[DocumentArray]:
        """Run segmentation"""
        for batch in docs.batch(self._batch_size):
            self._reshape_docs(batch)
            segmented = self._model.segment(batch_docs)
            self._update_blobs(batch, segmented)
        return docs
