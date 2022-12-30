# labeler-client
Client side programmatic python library for Labeler service
## To use in Python Notebook
![version](https://img.shields.io/badge/labeler--client%20latest-v1.0.4-blue)

You can use either `SSH` or `HTTPS` to install this python package
- Run `pip install git+ssh://git@github.com/rit-git/labeler-client.git`
- Run `pip install git+https://github.com/rit-git/labeler-client.git`
  - You may need to use [personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) instead of password
- To update the package: add `--upgrade` flag *(labeler widget `labeler-ui` is included in the installation)*.
- To install a specific version: add `@vx.x.x` tag after the github URL

```python
# To use library modules
from labeler_client import ...
```

We provide example notebooks demonstrating the basic and advanced functionalities under directory `Examples`
