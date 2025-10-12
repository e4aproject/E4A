#!/usr/bin/env node
import { spawn } from "child_process";
const args = process.argv.slice(2);
const proc = spawn("python", ["-m", "cli.cli_main", ...args], { stdio: "inherit" });
proc.on("exit", (code) => process.exit(code));
