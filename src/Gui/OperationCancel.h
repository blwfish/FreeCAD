// SPDX-License-Identifier: LGPL-2.1-or-later
/**
 * Global cancel flag for long-running C++ operations (Check Geometry, boolean fuse, etc.)
 *
 * Usage:
 *   - To request cancel: Gui::OperationCancel::request()
 *     (called from keyboard shortcut, external signal, etc.)
 *   - To check cancel:   Gui::OperationCancel::isSet()
 *     (called from operation's progress/UserBreak hook)
 *   - To reset:          Gui::OperationCancel::clear()
 *     (called at start/end of an operation)
 *
 * Thread-safe: all methods use std::atomic.
 */

#ifndef GUI_OPERATIONCANCEL_H
#define GUI_OPERATIONCANCEL_H

#include <atomic>

namespace Gui
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

}  // namespace Gui

#endif  // GUI_OPERATIONCANCEL_H
