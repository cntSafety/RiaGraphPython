#pragma once

#include <memory>
#include <string>
#include <unordered_map>

#include "common/exception/runtime.h"
#include "main/riag.h"
#include "main/prepared_statement.h"
#include "main/storage_driver.h"
#include "pybind_include.h"

struct PyDatabaseState {
    std::unique_ptr<riag::main::Database> database;
    std::unique_ptr<riag::main::StorageDriver> storageDriver;

    ~PyDatabaseState() { closeNative(); }

    void closeNative() {
        storageDriver.reset();
        database.reset();
    }

    riag::main::Database& ref() const {
        if (database == nullptr) {
            throw riag::common::RuntimeException("Database is closed.");
        }
        return *database;
    }

    riag::main::StorageDriver& storage() const {
        if (storageDriver == nullptr) {
            throw riag::common::RuntimeException("Database is closed.");
        }
        return *storageDriver;
    }
};

struct PyConnectionState {
    std::shared_ptr<PyDatabaseState> database;
    std::unique_ptr<riag::main::StorageDriver> storageDriver;
    std::unique_ptr<riag::main::Connection> conn;
    std::unordered_map<std::string, py::object> arrowTableRefs;

    ~PyConnectionState() { closeNative(); }

    void closeNative() {
        arrowTableRefs.clear();
        conn.reset();
        storageDriver.reset();
        database.reset();
    }

    riag::main::Connection& ref() const {
        if (conn == nullptr) {
            throw riag::common::RuntimeException("Connection is closed.");
        }
        return *conn;
    }

    riag::main::StorageDriver& storage() const {
        if (storageDriver == nullptr) {
            throw riag::common::RuntimeException("Connection is closed.");
        }
        return *storageDriver;
    }
};

struct PyPreparedStatementState {
    std::shared_ptr<PyConnectionState> connection;
    std::unique_ptr<riag::main::PreparedStatement> preparedStatement;

    riag::main::PreparedStatement& ref() const {
        if (preparedStatement == nullptr) {
            throw riag::common::RuntimeException("Prepared statement is closed.");
        }
        return *preparedStatement;
    }
};

struct PyQueryResultState {
    std::shared_ptr<PyConnectionState> connection;
    std::shared_ptr<PyQueryResultState> parent;
    std::unique_ptr<riag::main::QueryResult> owned;
    riag::main::QueryResult* borrowed = nullptr;

    riag::main::QueryResult& ref() const {
        auto* result = owned != nullptr ? owned.get() : borrowed;
        if (result == nullptr) {
            throw riag::common::RuntimeException("Query result is closed.");
        }
        return *result;
    }
};
