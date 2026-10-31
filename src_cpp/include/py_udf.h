#pragma once

#include <string>

#include "common/types/types.h"
#include "function/function.h"
#include "pybind_include.h"

using riag::common::LogicalTypeID;
using riag::function::function_set;

namespace riag {
namespace main {
class ClientContext;
} // namespace main
} // namespace riag

class PyUDF {

public:
    static function_set toFunctionSet(const std::string& name, const py::function& udf,
        const py::list& paramTypes, const std::string& resultType, bool defaultNull,
        bool catchExceptions, riag::main::ClientContext* context);
};
