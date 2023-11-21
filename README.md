# labeler-client
Client side programmatic python library for Labeler service
## To use in Python Notebook
![version](https://img.shields.io/badge/labeler--client%20latest-v1.4.6-blue)

## **Instructions**
1. Download [conda](https://conda.io/projects/conda/en/stable/user-guide/install/download.html)
2. Create a conda environment
   - Run `conda create -n <env_name> python=3.9`
   - Run `conda activate <env_name>`
3. Install MegAnno+ libs (following development labeler-client and labeler-ui)
    - Run `pip install "labeler_client[ui] @ git+ssh://git@github.com/rit-git/labeler-client.git"`
    - Or run `pip install "labeler_client[ui] @ git+https://github.com/rit-git/labeler-client.git"`
      - You may need to use [personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) instead of password<br/>

4. Set up OpenAI API Keys [using environment variables in place of your API key
](https://help.openai.com/en/articles/5112595-best-practices-for-api-key-safety#h_a1ab3ba7b2) (They stay in your browser; we don't store your OpenAI keys)

5. Explore in demo notebook
   - `pip install jupyter`
   - Run `jupyter notebook`
   - Open demo notebook (add link)


```python
# To use library modules
from labeler_client import ...
```

We provide example notebooks demonstrating the basic and advanced functionalities under directory `Examples`
