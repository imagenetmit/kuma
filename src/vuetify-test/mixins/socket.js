import { io } from "socket.io-client";

export default {
    data() {
        return {
            socket: null,
            monitorList: {},
            lastHeartbeatList: {},
            heartbeatList: {},
            stats: {
                up: 0,
                down: 0,
                pending: 0,
                active: 0,
                pause: 0,
            },
        };
    },
    methods: {
        initSocketIO() {
            if (this.socket) {
                return;
            }

            this.socket = io(window.location.origin, {
                path: "/socket.io/",
                transports: ["websocket"],
                reconnection: true,
                reconnectionAttempts: 5,
                reconnectionDelay: 1000,
                reconnectionDelayMax: 5000,
                timeout: 20000,
                autoConnect: true,
            });

            this.socket.on("connect", () => {
                console.log("Socket connected");
                this.getMonitorList();
            });

            this.socket.on("disconnect", () => {
                console.log("Socket disconnected");
            });

            this.socket.on("monitorList", (data) => {
                this.monitorList = data;
                this.updateStats();
            });

            this.socket.on("updateMonitorIntoList", (data) => {
                Object.entries(data).forEach(([monitorID, updatedMonitor]) => {
                    this.monitorList[monitorID] = updatedMonitor;
                });
                this.updateStats();
            });

            this.socket.on("deleteMonitorFromList", (monitorID) => {
                if (this.monitorList[monitorID]) {
                    delete this.monitorList[monitorID];
                }
                this.updateStats();
            });

            this.socket.on("lastHeartbeat", (data) => {
                this.lastHeartbeatList[data.monitorID] = data;
            });
            
            this.socket.on("heartbeat", (data) => {
                if (!(data.monitorID in this.heartbeatList)) {
                    this.heartbeatList[data.monitorID] = [];
                }

                this.heartbeatList[data.monitorID].push(data);

                if (this.heartbeatList[data.monitorID].length >= 150) {
                    this.heartbeatList[data.monitorID].shift();
                }
            });

            this.socket.on("heartbeatList", (monitorID, data, overwrite = false) => {
                if (!(monitorID in this.heartbeatList) || overwrite) {
                    this.heartbeatList[monitorID] = data;
                } else {
                    this.heartbeatList[monitorID] = data.concat(this.heartbeatList[monitorID]);
                }
            });
        },

        getMonitorList(callback) {
            if (!callback) {
                callback = () => {};
            }
            this.socket.emit("getMonitorList", callback);
        },

        updateStats() {
            this.stats = {
                up: 0,
                down: 0,
                pending: 0,
                active: 0,
                pause: 0,
            };

            Object.values(this.monitorList).forEach(monitor => {
                if (monitor.active) {
                    this.stats.active++;
                } else {
                    this.stats.pause++;
                }

                if (monitor.id in this.lastHeartbeatList) {
                    const status = this.lastHeartbeatList[monitor.id].status;
                    if (status === 1) {
                        this.stats.up++;
                    } else if (status === 0) {
                        this.stats.down++;
                    } else if (status === 2) {
                        this.stats.pending++;
                    }
                }
            });
        },

        getSocket() {
            return this.socket;
        },
    },
    mounted() {
        this.initSocketIO();
    },
    beforeUnmount() {
        if (this.socket) {
            this.socket.disconnect();
        }
    },
}; 