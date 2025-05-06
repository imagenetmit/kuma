export default {
    data() {
        return {
            system: (window.matchMedia("(prefers-color-scheme: dark)").matches) ? "dark" : "light",
            userTheme: localStorage.theme,
            userHeartbeatBar: localStorage.heartbeatBarTheme,
            styleElapsedTime: localStorage.styleElapsedTime,
        };
    },

    mounted() {
        console.log("Theme mixin mounted");
        console.log("Initial userHeartbeatBar:", this.userHeartbeatBar);
        
        // Default Theme
        if (!this.userTheme) {
            this.userTheme = "auto";
        }

        // Default Heartbeat Bar
        if (!this.userHeartbeatBar) {
            this.userHeartbeatBar = "normal";
            console.log("Setting default userHeartbeatBar to normal");
        }

        // Default Elapsed Time Style
        if (!this.styleElapsedTime) {
            this.styleElapsedTime = "no-line";
        }
        
        console.log("Final userHeartbeatBar value:", this.userHeartbeatBar);
    },

    watch: {
        userTheme(to) {
            localStorage.theme = to;
        },

        styleElapsedTime(to) {
            localStorage.styleElapsedTime = to;
        },

        userHeartbeatBar(to) {
            console.log("userHeartbeatBar changed to:", to);
            localStorage.heartbeatBarTheme = to;
        }
    }
}; 