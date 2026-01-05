"""RPC protocol implementation for NotebookLM batchexecute API."""

from .types import (
    RPCMethod,
    BATCHEXECUTE_URL,
    QUERY_URL,
    StudioContentType,
    AudioFormat,
    AudioLength,
    VideoFormat,
    VideoStyle,
    QuizQuantity,
    QuizDifficulty,
    InfographicOrientation,
    InfographicDetail,
    SlideDeckFormat,
    SlideDeckLength,
    ReportFormat,
)
from .encoder import encode_rpc_request, build_request_body
from .decoder import (
    strip_anti_xssi,
    parse_chunked_response,
    extract_rpc_result,
    decode_response,
    RPCError,
)

__all__ = [
    "RPCMethod",
    "BATCHEXECUTE_URL",
    "QUERY_URL",
    "StudioContentType",
    "AudioFormat",
    "AudioLength",
    "VideoFormat",
    "VideoStyle",
    "QuizQuantity",
    "QuizDifficulty",
    "InfographicOrientation",
    "InfographicDetail",
    "SlideDeckFormat",
    "SlideDeckLength",
    "ReportFormat",
    "encode_rpc_request",
    "build_request_body",
    "strip_anti_xssi",
    "parse_chunked_response",
    "extract_rpc_result",
    "decode_response",
    "RPCError",
]
