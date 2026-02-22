// SPDX-License-Identifier: LGPL-2.1-or-later
/**
 * Gui-namespace alias for Base::OperationCancel.
 *
 * The flag now lives in Base/ so App-layer code (Part, Mesh, …) can check it
 * without a Gui dependency.  Existing Gui code that uses Gui::OperationCancel
 * keeps compiling unchanged via the alias below.
 */

#ifndef GUI_OPERATIONCANCEL_H
#define GUI_OPERATIONCANCEL_H

#include <Base/OperationCancel.h>

namespace Gui
{
using OperationCancel = Base::OperationCancel;
}  // namespace Gui

#endif  // GUI_OPERATIONCANCEL_H
