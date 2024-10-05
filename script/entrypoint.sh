#!/usr/bin/env bash

echo "Instance: $1"


case "$1" in
  mage)
    echo "started mage container."
    exec mage start pipeline
    ;;
  *)
    echo "starting streamlit container."
    exec streamlit run app/app.py
    ;;
esac