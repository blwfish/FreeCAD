// SPDX-License-Identifier: LGPL-2.1-or-later
/**
 * Global cancel flag for long-running C++ operations.
 *
 * Lives in Base so both App-layer (Part, Mesh, …) and Gui-layer code can use it
 * without creating a Gui → App dependency inversion.
 *
 * Usage:
 *   - To request cancel: Base::OperationCancel::request()
 *     (from keyboard shortcut, MCP cancel_job, external signal, …)
 *   - To check cancel:   Base::OperationCancel::isSet()
 *     (from operation's progress/UserBreak hook)
 *   - To reset:          Base::OperationCancel::clear()
 *     (at the start and/or end of a cancellable operation)
 *
 * Thread-safe: all methods use std::atomic.
 */

#ifndef BASE_OPERATIONCANCEL_H
#define BASE_OPERATIONCANCEL_H

#include <atomic>

namespace Base
{

struct OperationCancel
{
    /// Atomic cancel flag.  Declared inline so no .cpp definition is needed.
    inline static std::atomic<bool> requested{false};

    /// Signal that the current long-running operation should stop.
    /// Safe to call from any thread at any time.
    static void request()
    {
        requested.store(true, std::memory_order_relaxed);
    }

    /// Returns true if a cancel has been requested since the last clear().
    static bool isSet()
    {
        return requested.load(std::memory_order_relaxed);
    }

    /// Reset the flag.  Call at the start (and/or end) of a cancellable operation.
    static void clear()
    {
        requested.store(false, std::memory_order_relaxed);
    }
};

}  // namespace Base

#endif  // BASE_OPERATIONCANCEL_H
