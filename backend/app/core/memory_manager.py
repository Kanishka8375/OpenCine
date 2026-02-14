from __future__ import annotations

import gc
import logging
import threading
from collections.abc import Callable
from typing import Any

import torch

logger = logging.getLogger(__name__)


class ModelManager:
    """Singleton VRAM manager that keeps only one heavy pipeline active on GPU."""

    _instance: 'ModelManager | None' = None
    _instance_lock = threading.Lock()

    def __new__(cls):
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._model_factories: dict[str, Callable[[], Any]] = {}
        self._models: dict[str, Any] = {}
        self._active_model: str | None = None
        self._lock = threading.Lock()

    def register_model(self, model_type: str, factory: Callable[[], Any]) -> None:
        logger.info('Registering model factory: %s', model_type)
        self._model_factories[model_type] = factory

    def _to_cpu(self, model_type: str) -> None:
        model = self._models.get(model_type)
        if model is None:
            return
        logger.info('Offloading model %s to CPU', model_type)
        model.to('cpu')

    @staticmethod
    def _clear_cuda() -> None:
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
        gc.collect()

    def load_model(self, model_type: str):
        """
        Ensures only one heavy model is resident on GPU.

        If the requested model is not active on GPU, currently active model is moved to CPU,
        CUDA cache is cleared, and requested model is moved to GPU.
        """
        with self._lock:
            if model_type not in self._model_factories:
                raise KeyError(f'No factory registered for model type: {model_type}')

            if self._active_model == model_type:
                logger.info('Model %s already active on GPU', model_type)
                return self._models[model_type]

            if self._active_model is not None:
                self._to_cpu(self._active_model)
                self._clear_cuda()

            if model_type not in self._models:
                logger.info('Instantiating model: %s', model_type)
                self._models[model_type] = self._model_factories[model_type]()

            logger.info('Moving model %s to CUDA', model_type)
            self._models[model_type].to('cuda')
            self._active_model = model_type
            return self._models[model_type]


model_manager = ModelManager()
