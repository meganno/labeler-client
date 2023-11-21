import { FocusStyleManager } from "@blueprintjs/core";
import "@blueprintjs/core/lib/css/blueprint.css";
import "@blueprintjs/icons/lib/css/blueprint-icons.css";
import _ from "lodash";
import "normalize.css/normalize.css";
FocusStyleManager.onlyShowFocusOnTabs();
export default function App({ Component, pageProps }) {
    if (_.isEqual(typeof window, "object")) return <Component {...pageProps} />;
    return null;
}
