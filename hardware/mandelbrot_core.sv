module mandelbrot_core #(
    parameter int MAX_ITER = 120
)(
    input  logic               clk,
    input  logic               rst_n,
    input  logic               ce,          // run fractal math only when CE is high
    input  logic               start,
    input  logic signed [31:0] c_re_q28,
    input  logic signed [31:0] c_im_q28,

    output logic               busy,
    output logic               done,
    output logic [15:0]        iter_count
);

    typedef enum logic [1:0] {S_IDLE, S_RUN, S_FINISH} state_t;
    state_t state;

    // z = x + jy in Q4.28
    logic signed [31:0] x, y;

    logic [15:0] iter;

    // Math intermediates: Q8.56
    logic signed [63:0] x2, y2, xy2;
    logic signed [63:0] mag2;
    logic signed [63:0] new_x64, new_y64;

    // Clamped intermediates
    logic signed [63:0] new_x_clamped, new_y_clamped;

    // Rescaled values
    logic signed [31:0] new_x_q28, new_y_q28;

    // Escape threshold: |z|^2 >= 4.0 in Q8.56
    localparam logic signed [63:0] ESCAPE_THRESH = (64'sd4) <<< 56;

    // ============================================================
    // Combinational math
    // ============================================================
    always_comb begin
        x2   = $signed(x) * $signed(x);
        y2   = $signed(y) * $signed(y);
        xy2  = ($signed(x) * $signed(y)) <<< 1;
        mag2 = x2 + y2;

        // z^2 + c (Q8.56)
        new_x64 = (x2 - y2) + ($signed(c_re_q28) <<< 28);
        new_y64 = xy2       + ($signed(c_im_q28) <<< 28);

        // ========================================================
        // Clamp to prevent overflow artifacts (horizontal streak)
        // ========================================================
        if (new_x64 > 64'sh3FFF_FFFF_FFFF_FFFF)
            new_x_clamped = 64'sh3FFF_FFFF_FFFF_FFFF;
        else if (new_x64 < -64'sh3FFF_FFFF_FFFF_FFFF)
            new_x_clamped = -64'sh3FFF_FFFF_FFFF_FFFF;
        else
            new_x_clamped = new_x64;

        if (new_y64 > 64'sh3FFF_FFFF_FFFF_FFFF)
            new_y_clamped = 64'sh3FFF_FFFF_FFFF_FFFF;
        else if (new_y64 < -64'sh3FFF_FFFF_FFFF_FFFF)
            new_y_clamped = -64'sh3FFF_FFFF_FFFF_FFFF;
        else
            new_y_clamped = new_y64;

        // Back to Q4.28
        new_x_q28 = $signed(new_x_clamped >>> 28);
        new_y_q28 = $signed(new_y_clamped >>> 28);
    end

    // ============================================================
    // FSM
    // ============================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state      <= S_IDLE;
            x          <= 32'sd0;
            y          <= 32'sd0;
            iter       <= 16'd0;
            busy       <= 1'b0;
            done       <= 1'b0;
            iter_count <= 16'd0;
        end else begin
            case (state)
                S_IDLE: begin
                    done <= 1'b0;
                    busy <= 1'b0;

                    if (start) begin
                        x     <= 32'sd0;
                        y     <= 32'sd0;
                        iter  <= 16'd0;
                        busy  <= 1'b1;
                        state <= S_RUN;
                    end
                end

                S_RUN: begin
                    busy <= 1'b1;

                    if (ce) begin
                        if (mag2 >= ESCAPE_THRESH) begin
                            iter_count <= iter;
                            done       <= 1'b1;
                            busy       <= 1'b0;
                            state      <= S_FINISH;
                        end else if (iter >= MAX_ITER[15:0]) begin
                            iter_count <= iter;
                            done       <= 1'b1;
                            busy       <= 1'b0;
                            state      <= S_FINISH;
                        end else begin
                            x    <= new_x_q28;
                            y    <= new_y_q28;
                            iter <= iter + 16'd1;
                        end
                    end
                end

                S_FINISH: begin
                    busy <= 1'b0;

                    if (!start) begin
                        done  <= 1'b0;
                        state <= S_IDLE;
                    end
                end

                default: state <= S_IDLE;
            endcase
        end
    end

endmodule