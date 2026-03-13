`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 12/27/2025 06:37:28 PM
// Design Name: 
// Module Name: EEG_Packet_Parser
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////

(* keep_hierarchy = "yes" *)
module EEG_Packet_Parser #(
    parameter logic [7:0] SYNC1      = 8'hAA,
    parameter logic [7:0] SYNC2      = 8'h55,
    parameter logic [7:0] EXPECT_LEN = 8'd8
)(
    input  logic        i_Clock,
    input  logic        i_Reset,        //synchronous reset

    input  logic        i_Rx_DV,         //1-cycle pulse when byte is valid
    input  logic [7:0]  i_Rx_Byte,

    output logic        o_Packet_Valid,  //1-cycle pulse on good packet
    output logic [15:0] o_Alpha,
    output logic [15:0] o_Beta,
    output logic [15:0] o_Theta,
    output logic [15:0] o_Delta,

    //debug taps (helpful + prevents trimming)
    output logic [7:0]  o_State,
    output logic [7:0]  o_Last_Byte,
    output logic [7:0]  o_Check_Xor
);

    typedef enum logic [2:0] {
        S_WAIT_SYNC1   = 3'd0,
        S_WAIT_SYNC2   = 3'd1,
        S_WAIT_LEN     = 3'd2,
        S_READ_PAYLOAD = 3'd3,
        S_READ_CHK     = 3'd4
    } state_t;

    state_t state;

    logic [7:0] len;
    logic [2:0] idx;              
    logic [7:0] chk_xor;
    logic [7:0] payload [0:7];

    (* keep = "true" *) logic [15:0] alpha_r, beta_r, theta_r, delta_r;

    assign o_Alpha = alpha_r;
    assign o_Beta  = beta_r;
    assign o_Theta = theta_r;
    assign o_Delta = delta_r;

    always_ff @(posedge i_Clock) begin
        if (i_Reset) begin
            state          <= S_WAIT_SYNC1;
            len            <= 8'd0;
            idx            <= 3'd0;
            chk_xor        <= 8'd0;
            o_Packet_Valid <= 1'b0;

            alpha_r        <= 16'd0;
            beta_r         <= 16'd0;
            theta_r        <= 16'd0;
            delta_r        <= 16'd0;

            o_State        <= 8'd0;
            o_Last_Byte    <= 8'd0;
            o_Check_Xor    <= 8'd0;
        end else begin
            o_Packet_Valid <= 1'b0;
            o_State        <= {5'd0, state};
            o_Check_Xor    <= chk_xor;

            if (i_Rx_DV) begin
                o_Last_Byte <= i_Rx_Byte;

                unique case (state)
                    S_WAIT_SYNC1: begin
                        if (i_Rx_Byte == SYNC1) state <= S_WAIT_SYNC2;
                        else                    state <= S_WAIT_SYNC1;
                    end

                    S_WAIT_SYNC2: begin
                        if (i_Rx_Byte == SYNC2) state <= S_WAIT_LEN;
                        else if (i_Rx_Byte == SYNC1) state <= S_WAIT_SYNC2; //overlap-friendly
                        else state <= S_WAIT_SYNC1;
                    end

                    S_WAIT_LEN: begin
                        len     <= i_Rx_Byte;
                        chk_xor <= i_Rx_Byte;     //XOR starts with LEN
                        idx     <= 3'd0;

                        if (i_Rx_Byte == EXPECT_LEN) state <= S_READ_PAYLOAD;
                        else                         state <= S_WAIT_SYNC1;
                    end

                    S_READ_PAYLOAD: begin
                        payload[idx] <= i_Rx_Byte;
                        chk_xor      <= chk_xor ^ i_Rx_Byte;

                        if (idx == 3'd7) state <= S_READ_CHK;
                        else             idx   <= idx + 3'd1;
                    end

                    S_READ_CHK: begin
                        if (i_Rx_Byte == chk_xor) begin
                            //big-endian 4x uint16
                            alpha_r <= {payload[0], payload[1]};
                            beta_r  <= {payload[2], payload[3]};
                            theta_r <= {payload[4], payload[5]};
                            delta_r <= {payload[6], payload[7]};

                            o_Packet_Valid <= 1'b1;
                        end
                        state <= S_WAIT_SYNC1;
                    end

                    default: state <= S_WAIT_SYNC1;
                endcase
            end
        end
    end

endmodule


