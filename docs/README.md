# Website

This website is built using [Docusaurus 2](https://docusaurus.io/).

### Installation

```
$ yarn
```

or

```
npm install
```

### Local Development

```
$ yarn start
```

or

```
npm start
```

This command starts a local development server and opens up a browser window. Most changes are reflected live without having to restart the server.

### Build

```
$ yarn build
```

or

```
npm run build
```

This command generates static content into the `build` directory and can be served using any static contents hosting service.

It's important that you build the documentation using `yarn build` **before pushing to `main`**. After building,
check that everything works, such as syntax highlighting etc.

If there are issues, please try
* to run `npm run clear` or `yarn clear`
* delete `package-lock.json` and re-.install packages


### Deployment

GitHub actions takes care of deployment. Any changes to the `docs` folder on the `main` branch will trigger
the pipeline. You can see the documentation live at https://vibber-ai.github.io/fastapi-azure-auth/, and browse
the static files in the `gh-pages` branch.
