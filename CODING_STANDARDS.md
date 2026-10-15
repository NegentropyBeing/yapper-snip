# Coding standards

Read during review. Mechanical rules (where `os._exit`, variant file names and the GPU lock may appear) live in `tests/test_architecture.py`; this file holds the judgement calls.

- A background job gets a `start_*` function in `app/tasks.py` that validates, then calls `jobs.submit`. Routes in `app/main.py` only parse the request, call, and translate errors to HTTP.
- Tests cross a module's interface. Patching a module-level location (`clips.WORK_DIR`, `models.MODELS_DIR`) is fine; patching a collaborator to reach inside is a sign the interface is the wrong shape.
- State shared by several features (the GPU, loaded models, the folder layout of a Clip) belongs to the one module that owns it. Name the owner in the diff when adding to it.
- Domain words follow `GLOSSARY.md`. A new concept that needs a name goes in the glossary in the same change.
