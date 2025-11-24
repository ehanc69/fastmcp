"""
⚠️ TEMPORARY CODE - SEP-1686 WORKAROUND FOR MCP SDK LIMITATION ⚠️

This file contains a workaround for one remaining MCP SDK limitation related to SEP-1686 tasks:

1. Client capability declaration - SDK doesn't support customizing experimental capabilities
   during ClientSession initialization (hardcodes experimental=None)

The SDK now provides native support for:
- Task protocol types (GetTaskResult, Task, TaskStatus, etc.)
- Task notifications (TaskStatusNotification)
- Client-side experimental task APIs (session.experimental.get_task())

This shim will be removed when the SDK allows setting capabilities during session init.

DO NOT WRITE TESTS FOR THIS FILE - these are temporary hacks.
"""

import mcp.types
from mcp.client.session import (
    SUPPORTED_PROTOCOL_VERSIONS,
    ClientSession,
    _default_elicitation_callback,
    _default_list_roots_callback,
    _default_sampling_callback,
)

# ═══════════════════════════════════════════════════════════════════════════
# 1. Client Capability Declaration
# ═══════════════════════════════════════════════════════════════════════════


async def task_capable_initialize(
    session: ClientSession,
) -> mcp.types.InitializeResult:
    """Initialize a session with task capabilities.

    Args:
        session: The ClientSession to initialize

    Returns:
        InitializeResult from the server
    """
    # Build capabilities
    sampling = (
        mcp.types.SamplingCapability()
        if session._sampling_callback != _default_sampling_callback
        else None
    )
    elicitation = (
        mcp.types.ElicitationCapability()
        if session._elicitation_callback != _default_elicitation_callback
        else None
    )
    roots = (
        mcp.types.RootsCapability(listChanged=True)
        if session._list_roots_callback != _default_list_roots_callback
        else None
    )

    # Send initialize request with task capability
    result = await session.send_request(
        mcp.types.ClientRequest(
            mcp.types.InitializeRequest(
                params=mcp.types.InitializeRequestParams(
                    protocolVersion=mcp.types.LATEST_PROTOCOL_VERSION,
                    capabilities=mcp.types.ClientCapabilities(
                        sampling=sampling,
                        elicitation=elicitation,
                        experimental={"tasks": {}},
                        roots=roots,
                    ),
                    clientInfo=session._client_info,
                ),
            )
        ),
        mcp.types.InitializeResult,
    )

    # Validate protocol version
    if result.protocolVersion not in SUPPORTED_PROTOCOL_VERSIONS:
        raise RuntimeError(
            f"Unsupported protocol version from the server: {result.protocolVersion}"
        )

    # Send initialized notification
    await session.send_notification(
        mcp.types.ClientNotification(mcp.types.InitializedNotification())
    )

    return result
