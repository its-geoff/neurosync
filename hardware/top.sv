`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 11/13/2025 09:50:10 PM
// Design Name: 
// Module Name: top
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

module UART_RX_To_7_Seg_Top (
    input  logic        i_Clock,       //E3  100 MHz
    input  logic        i_RX_Serial,   //C4  UART RX
    output logic        o_TX_Serial,   //D4  UART TX (loopback)

    output logic [6:0]  seg,           //7-segment cathodes
    output logic [7:0]  an,            //7-segment anodes
    output logic        dp,            //decimal point

    output logic        LED0,          //pulses on valid EEG packet

    //VGA outputs
    output logic [3:0]  vgaRed,
    output logic [3:0]  vgaGreen,
    output logic [3:0]  vgaBlue,
    output logic        Hsync,
    output logic        Vsync
);

    //Power-on reset  (~167 ms at 100 MHz)
    localparam int CLKS_PER_BIT = 868;

    logic [23:0] por_cnt = 24'd0;
    logic        reset   = 1'b1;

    always_ff @(posedge i_Clock) begin
        if (por_cnt != 24'hFFFFFF) begin
            por_cnt <= por_cnt + 24'd1;
            reset   <= 1'b1;
        end else begin
            reset   <= 1'b0;
        end
    end

    //UART RX
    logic       rx_dv;
    logic [7:0] rx_byte;

    (* dont_touch = "true" *)
    UART_RX #(.CLKS_PER_BIT(CLKS_PER_BIT)) u_uart_rx (
        .i_Clock     (i_Clock),
        .i_RX_Serial (i_RX_Serial),
        .o_RX_DV     (rx_dv),
        .o_RX_Byte   (rx_byte)
    );

    //UART TX (loopback echo)
    logic       tx_dv;
    logic [7:0] tx_byte;
    logic       tx_active;
    logic       tx_done;

    always_ff @(posedge i_Clock) begin
        if (reset) begin
            tx_dv   <= 1'b0;
            tx_byte <= 8'd0;
        end else begin
            tx_dv <= 1'b0;
            if (rx_dv && !tx_active) begin
                tx_byte <= rx_byte;
                tx_dv   <= 1'b1;
            end
        end
    end

    (* dont_touch = "true" *)
    UART_TX #(.CLKS_PER_BIT(CLKS_PER_BIT)) u_uart_tx (
        .i_Clock     (i_Clock),
        .i_TX_DV     (tx_dv),
        .i_TX_Byte   (tx_byte),
        .o_TX_Active (tx_active),
        .o_TX_Serial (o_TX_Serial),
        .o_TX_Done   (tx_done)
    );

    //EEG Packet Parser
    logic        packet_valid;
    logic [15:0] alpha, beta, theta, delta;

    logic [7:0]  p_state, p_last, p_xor;   //debug ports

    EEG_Packet_Parser u_parser (
        .i_Clock        (i_Clock),
        .i_Reset        (reset),

        .i_Rx_DV        (rx_dv),
        .i_Rx_Byte      (rx_byte),

        .o_Packet_Valid (packet_valid),
        .o_Alpha        (alpha),
        .o_Beta         (beta),
        .o_Theta        (theta),
        .o_Delta        (delta),

        .o_State        (p_state),
        .o_Last_Byte    (p_last),
        .o_Check_Xor    (p_xor)
    );

    //LED0 - pulse stretcher on packet_valid (~10 ms visible blink at 50 Hz)
    logic [22:0] led_cnt;

    always_ff @(posedge i_Clock) begin
        if (reset) begin
            led_cnt <= 23'd0;
        end else begin
            if (packet_valid)
                led_cnt <= 23'd1_000_000;
            else if (led_cnt != 0)
                led_cnt <= led_cnt - 23'd1;
        end
    end

    assign LED0 = (led_cnt != 0);

    //7-segment display - shows alpha[7:0] as two hex digits
    (* keep = "true" *) logic [7:0] display_byte_r;

    always_ff @(posedge i_Clock) begin
        if (reset)
            display_byte_r <= 8'h00;
        else if (packet_valid)
            display_byte_r <= alpha[7:0];
    end

    SevenSeg_2Digit_Mux u_disp (
        .i_Clock (i_Clock),
        .i_Reset (reset),
        .i_Byte  (display_byte_r),
        .seg     (seg),
        .an      (an),
        .dp      (dp)
    );

    //VGA - internal signals
    logic        vga_reset;
    logic [9:0]  vga_x, vga_y;
    logic        vga_active;
    logic        vga_hsync_raw, vga_vsync_raw;
    logic [3:0]  vga_red_raw, vga_green_raw, vga_blue_raw;

    assign vga_reset = reset;

    //VGA timing  (contains its own 100 MHz -> 25 MHz CE divider)
    VGA_640x480_Timing u_vga_timing (
        .i_Clock  (i_Clock),
        .i_Reset  (vga_reset),
        .o_HSync  (vga_hsync_raw),
        .o_VSync  (vga_vsync_raw),
        .o_X      (vga_x),
        .o_Y      (vga_y),
        .o_Active (vga_active)
    );

    //VGA pixel renderer - abstract brainwave aurora
    VGA_EEG_Abstract u_vga_abstract (
        .i_Clock  (i_Clock),
        .i_Reset  (vga_reset),
        .i_Active (vga_active),
        .i_X      (vga_x),
        .i_Y      (vga_y),
        .i_VSync  (vga_vsync_raw),

        .i_Delta  (delta),
        .i_Theta  (theta),
        .i_Alpha  (alpha),
        .i_Beta   (beta),

        .o_Red    (vga_red_raw),
        .o_Green  (vga_green_raw),
        .o_Blue   (vga_blue_raw)
    );

    //Drive top-level VGA outputs
    assign Hsync    = vga_hsync_raw;
    assign Vsync    = vga_vsync_raw;
    assign vgaRed   = vga_red_raw;
    assign vgaGreen = vga_green_raw;
    assign vgaBlue  = vga_blue_raw;

endmodule

