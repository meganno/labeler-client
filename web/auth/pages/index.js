import { actionToaster, createToast } from "@/components/toaster";
import {
    Button,
    Callout,
    Classes,
    Colors,
    Dialog,
    DialogBody,
    InputGroup,
    Intent,
    Radio,
    RadioGroup,
} from "@blueprintjs/core";
import { deleteApp, getApp, initializeApp } from "firebase/app";
import { GoogleAuthProvider, getAuth, signInWithPopup } from "firebase/auth";
import Head from "next/head";
import { useEffect, useState } from "react";
export default function Home() {
    const FIREBASE_CONFIG = {
        megagon: {
            apiKey: "AIzaSyDvr7chb86svObyDZXA7LYHHSMT2LRonNs",
            authDomain: "labeler-da2a3.firebaseapp.com",
            projectId: "labeler-da2a3",
            storageBucket: "labeler-da2a3.appspot.com",
            messagingSenderId: "621909423724",
            appId: "1:621909423724:web:73f1451bb274aa15970a49",
            measurementId: "G-6BF6D12LRQ",
        },
        indeed: {
            apiKey: "AIzaSyCo2VGxPNnH-DdysfXiEaC4djwuRbZsqo4",
            authDomain: "labeler-indeed.firebaseapp.com",
            projectId: "labeler-indeed",
            storageBucket: "labeler-indeed.appspot.com",
            messagingSenderId: "2754107042",
            appId: "1:2754107042:web:7283ec3a34898b1da029fb",
            measurementId: "G-MDLQJD46YT",
        },
    };
    const [loading, setLoading] = useState(false);
    const [org, setOrg] = useState("megagon");
    const [done, setDone] = useState(false);
    useEffect(() => {
        let config = _.get(FIREBASE_CONFIG, org, {});
        try {
            deleteApp(getApp()).then(() => initializeApp(config));
        } catch (error) {
            initializeApp(config);
        }
    }, [org]);
    const signInWithGoogle = () => {
        setLoading(true);
        const auth = getAuth();
        const provider = new GoogleAuthProvider();
        signInWithPopup(auth, provider)
            .then((result) => {
                const accessToken = _.get(result, "user.accessToken", null);
                const server = "localhost:52236";
                const socket = new WebSocket(`ws://${server}`);
                socket.onopen = () => {
                    socket.send(accessToken);
                    setDone(true);
                    socket.close();
                };
                socket.onerror = () => {
                    actionToaster.show(
                        createToast({
                            intent: Intent.DANGER,
                            message: `WebSocket connection to 'ws://${server}' failed.`,
                        })
                    );
                    setLoading(false);
                };
            })
            .catch((error) => {
                actionToaster.show(
                    createToast({
                        intent: Intent.DANGER,
                        message: `${error.code ? `[${error.code}]` : ""} ${
                            error.message
                        }`,
                    })
                );
                setLoading(false);
            });
    };
    return (
        <>
            <Head>
                <title>labeler_client</title>
                <meta
                    name="viewport"
                    content="width=device-width, initial-scale=1"
                />
                <link rel="icon" href="/images/favicon.ico" />
            </Head>
            {done ? (
                <div style={{ padding: 15 }}>
                    <Callout intent={Intent.SUCCESS}>
                        Authentication details received, processing details. You
                        may close this window at any time.
                    </Callout>
                </div>
            ) : (
                <Dialog
                    style={{ width: 237, backgroundColor: Colors.WHITE }}
                    isCloseButtonShown={false}
                    title={
                        <div style={{ padding: "0px 5px" }}>Authentication</div>
                    }
                    isOpen
                >
                    <DialogBody>
                        <div style={{ padding: 5 }}>
                            <RadioGroup
                                disabled={loading}
                                selectedValue={org}
                                onChange={(event) => setOrg(event.target.value)}
                                inline
                            >
                                <Radio label="Megagon" value="megagon" />
                                <Radio label="Indeed" value="indeed" />
                            </RadioGroup>
                            <Button
                                outlined
                                minimal
                                loading={loading}
                                icon={
                                    <img
                                        style={{ height: 16 }}
                                        className={Classes.ICON}
                                        src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg"
                                    />
                                }
                                text="Sign in with Google"
                                onClick={signInWithGoogle}
                            />
                            {/* hidden element to remove focus on html tag */}
                            <div
                                style={{
                                    height: 0,
                                    overflow: "hidden",
                                    opacity: 0,
                                }}
                            >
                                <InputGroup autoFocus />
                            </div>
                        </div>
                    </DialogBody>
                </Dialog>
            )}
        </>
    );
}
