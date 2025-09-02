//
//  Logger.cpp
//  GameLib
//
//  Created by Eric Zinda on 5/19/15.
//  Copyright (c) 2015 Eric Zinda. All rights reserved.
//
#include "Logger.h"
#include <memory>
#include <iostream>
#include <fstream>
#include <sstream>

static std::unique_ptr<std::ofstream> g_logFile = nullptr;

// Function pointer for trace callback (defined by PythonInterface.cpp)
typedef void (*TraceCallback)(const char* message);

// Declare the function to get callback from PythonInterface
extern "C" TraceCallback GetTraceCallback();

void DebugLogMessage(int traceType, const TraceDetail levelOfDetail, const char *message)
{
	// Get callback dynamically from PythonInterface
	TraceCallback callback = GetTraceCallback();
	
	// Use callback if set, otherwise default to stdout
	if(callback) {
		callback(message);
	} else {
		std::cout << message;
	}
	
	// Also output to file if enabled
	if(g_logFile && g_logFile->is_open()) {
		(*g_logFile) << message;
		g_logFile->flush();
	}
}

void DebugLogMessagesToFile(const std::string &filename)
{
	// Close existing file if open
	if(g_logFile) {
		g_logFile.reset();
	}
	
	// If filename is provided, open new file
	if(filename.size() > 0) {
		g_logFile = std::make_unique<std::ofstream>(filename, std::ios::out | std::ios::trunc);
		if(g_logFile->is_open()) {
			(*g_logFile) << "Begin Logging\n";
			g_logFile->flush();
		}
	}
}
