#!/usr/bin/env bash

uvicorn main:app --proxy-headers --host 0.0.0.0 --reload