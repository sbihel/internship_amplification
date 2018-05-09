from setuptools import setup

setup(name='pr_message_gen',
      version='0.1',
      description='PR message generator for DSpot amplified test cases.',
      url='https://github.com/sbihel/internship_amplification',
      author='Simon Bihel',
      author_email='simon.bihel@ens-rennes.fr',
      license='MIT',
      packages=['pr_message_gen'],
      install_requires=[
          'gitpython',
          'javalang',
      ],
      zip_safe=False)
