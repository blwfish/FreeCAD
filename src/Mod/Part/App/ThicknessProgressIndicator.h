// SPDX-License-Identifier: LGPL-2.1-or-later
/**
 * Lightweight OCC Message_ProgressIndicator that makes BRepOffsetAPI_MakeThickSolid
 * (and other OCC algorithms that accept a Message_ProgressRange) cancellable via
 * Base::OperationCancel — no Qt required.
 *
 * Usage:
 *   Base::OperationCancel::clear();
 *   Handle(ThicknessProgressIndicator) pi = new ThicknessProgressIndicator();
 *   Message_ProgressRange range = pi->Start();
 *   mkThick.MakeThickSolidByJoin(..., Standard_False, range);
 *   if (Base::OperationCancel::isSet()) { // was cancelled }
 */

#ifndef PART_THICKNESSINDICATOR_H
#define PART_THICKNESSINDICATOR_H

#include <Message_ProgressIndicator.hxx>
#include <Base/OperationCancel.h>

class ThicknessProgressIndicator : public Message_ProgressIndicator
{
public:
    DEFINE_STANDARD_RTTI_INLINE(ThicknessProgressIndicator, Message_ProgressIndicator)

    /// No-op: we have no UI to update.
    void Show(const Message_ProgressScope& /*theScope*/,
              Standard_Boolean /*isForce*/) override
    {}

    /// Returns Standard_True when Base::OperationCancel::isSet() — safe to call
    /// from any thread (the atomic load is lock-free).
    Standard_Boolean UserBreak() override
    {
        return Base::OperationCancel::isSet() ? Standard_True : Standard_False;
    }
};

#endif  // PART_THICKNESSINDICATOR_H
